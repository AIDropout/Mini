from datetime import datetime
from typing import Callable, Dict, List, Optional, cast

from config.config import (
    AutoDBConfig,
    DataAction,
    DatabaseColumn,
    DatabaseTable,
    DataLocation,
    TableType,
)
from zootopia.storage.database.database import Database
from archive._intent import IntentManager
from zootopia.agent.intent.models import IntentConfig, IntentFilters
from zootopia.llm.llm import LLM
from zootopia.core.logger import logger
from zootopia.core.utils.utils import clean_and_parse_llm_json_output, render_jinja_template


class AutoDB:
    """Class for automating database operations using a language model."""

    def __init__(
        self,
        autodb_llm: LLM,
        intent_detector: IntentManager,
        col_to_llm_struct: dict,
        json_filter_formatter: Optional[Callable[[Dict], Dict]] = None,
    ) -> None:
        """Initialize the AutoDB instance."""
        self.intent_detector = intent_detector
        self.col_to_llm_struct = col_to_llm_struct
        self.autodb_llm = autodb_llm
        self.json_filter_formatter = json_filter_formatter

    @classmethod
    def from_config(cls, config: AutoDBConfig) -> "AutoDB":
        """Create an AutoDB instance from a configuration."""
        config.database_tables = [
            table for table in config.database_tables if table.llm_control
        ]  # removing all tables that the llm should not have access to

        database_info = cls._load_database_information(config.database_tables)
        intent_filters = database_info["intent_filters"]
        intent_detector_config = IntentConfig(
            llm_config=config.intent_llm_config, filters=intent_filters
        )
        intent_detector = IntentManager.from_config(intent_detector_config)

        autodb_llm = LLM(config.intent_llm_config)

        col_to_llm_struct = database_info["column_to_llm_structure"]

        return cls(
            autodb_llm=autodb_llm,
            intent_detector=intent_detector,
            col_to_llm_struct=col_to_llm_struct,
        )

    @classmethod
    def _col_llm_structure(cls, column: DatabaseColumn | List[DatabaseColumn]):
        """Generate the LLM structure for a single column or a list of columns."""
        if isinstance(column, List):
            return {
                col.name: f"({col.datatype.value}) {col.description}" for col in column
            }

        return {column.name: f"({column.datatype.value}) {column.description}"}

    @classmethod
    def _load_database_information(cls, database_tables: List[DatabaseTable]) -> dict:
        """Load database information from a list of database tables."""
        intent_filters = []
        column_to_llm_structure = {}

        for table in database_tables:
            if table.table_type is TableType.ROW:
                title = table.name.upper()

                intent_filters.append(
                    IntentFilters(
                        title=title,
                        description=table.description,
                    )
                )

                column_to_llm_structure[title] = cls._col_llm_structure(table.columns)
            elif table.table_type is TableType.COL:
                for column in table.columns:
                    title = f"{table.name.upper()}_{column.name.upper()}"

                    intent_filters.append(
                        IntentFilters(
                            title=title,
                            description=column.description,
                        )
                    )

                    column_to_llm_structure[title] = cls._col_llm_structure(column)

        return {
            "intent_filters": intent_filters,
            "column_to_llm_structure": column_to_llm_structure,
        }

    def save_data(self, data: str, database: Database):
        """Save data to the database based on user input."""
        data_locations = self._get_intents(data)
        logger.info(data_locations)
        data_actions = self._data_extraction(data, data_locations)
        logger.info(data_actions)
        self._update_database(database, data_actions)
        return data_locations, data_actions

    def get_data(self, data: str, database: Database):
        "Retrieve data from the database based on user input."
        data_locations = self._get_intents(data)
        data_rows = []
        for loc in data_locations:
            data_rows.extend(database.get_rows(table_name=loc.table.lower())[0][1])
        logger.info(data_rows)
        return data_rows

    def _get_intents(self, data: str) -> List[DataLocation]:
        """Get the intents from the user input."""
        intents = self.intent_detector.detect_intent(data)

        data_locations = [
            DataLocation(
                table=intent if "_" not in intent else intent[: intent.find("_")],
                column=None if "_" not in intent else intent[intent.find("_") + 1 :],
            )
            for intent in intents
        ]

        return data_locations

    def _data_extraction(
        self, data: str, data_locations: List[DataLocation]
    ) -> List[DataAction]:
        """Extract data from the user input based on the detected intents."""
        output = []

        for location in data_locations:
            location_str = (
                f"{location.table}_{location.column}"
                if location.column
                else location.table
            )
            structured_output = self.col_to_llm_struct[location_str]
            self.autodb_llm.system_prompt = render_jinja_template(
                "extraction.jinja",
                "zootopia/autodb/templates",
                response_structure=structured_output,
                date=datetime.now().isoformat(),
            )
            content = self.autodb_llm.generate_response(data).content
            cleaned = clean_and_parse_llm_json_output(content)
            if self.json_filter_formatter is not None:
                cleaned = self.json_filter_formatter(cleaned)
            output.append(DataAction(data_location=location, data=cleaned))

        return output

    # TODO: check if data exists already in the database (if it does, don't update db)
    def _update_database(self, database: Database, data_actions: List[DataAction]):
        """Update the database with the extracted data."""
        output = []

        for action in data_actions:
            if action.data_location.column is not None:
                output += database.update_cell(
                    table_name=action.data_location.table.lower(),
                    column_name=action.data_location.column.lower(),
                    new_value=list(action.data.values())[0],
                )
            else:
                output += database.insert(
                    table_name=action.data_location.table.lower(),
                    row_data=action.data,
                )

        return output

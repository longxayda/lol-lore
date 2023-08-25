import typing as T
import modules.general.constants
import modules.general.utilities
import psycopg2
import psycopg2.sql
import psycopg2.extensions
import collections.abc


class Database:
    def __init__(self, *args, **kwargs) -> None:
        self.conn: psycopg2.extensions.connection = psycopg2.connect(*args, **kwargs)
        self.cursor: psycopg2.extensions.cursor = self.conn.cursor()

    def insert(
        self,
        table: str,
        fields: T.List[str],
        data: T.Iterable[T.Any],
        on_conflict: T.Dict[str, str] = None,
        execute=True,
    ):
        def generate_query():
            initial_insert_query = "INSERT INTO {table} ({fields}) VALUES ({values})%s;"
            new_table = psycopg2.sql.Identifier(table)
            new_fields = psycopg2.sql.SQL(", ").join(
                map(psycopg2.sql.Identifier, fields)
            )
            new_values = psycopg2.sql.SQL(", ").join(
                psycopg2.sql.Placeholder() * len(fields)
            )
            if on_conflict is None:
                initial_insert_query = initial_insert_query % ""
            else:
                on_conflict_string = " ON CONFLICT (%s) DO %%s"
                if "ref" not in on_conflict or not on_conflict["ref"]:
                    raise Exception("No conflict field or constraint specified")
                conflict_fields = psycopg2.sql.SQL(", ").join(
                    map(psycopg2.sql.Identifier, on_conflict["ref"])
                )
                on_conflict_string = on_conflict_string % conflict_fields.as_string(
                    self.conn
                )
                if "update" not in on_conflict or not on_conflict["update"]:
                    on_conflict_string = on_conflict_string % "NOTHING"
                else:
                    on_conflict_string = on_conflict_string % "UPDATE SET %s"

                stringed_conflict_string = ", ".join(
                    [
                        f"{resolve_field}={on_conflict['update'][resolve_field]}"
                        for resolve_field in on_conflict["update"]
                    ]
                )
                on_conflict_string = on_conflict_string % stringed_conflict_string
                initial_insert_query = initial_insert_query % on_conflict_string

            insert_query = psycopg2.sql.SQL(initial_insert_query).format(
                table=new_table, fields=new_fields, values=new_values
            )
            return insert_query

        query = generate_query()
        if execute:
            if isinstance(data, collections.abc.Iterable):
                self.cursor.execute(query, data)
                self.conn.commit()
            else:
                raise Exception("Data is not an iterable object")

    def drop(self, table: str, is_cascade=False, execute=True):
        def generate_query():
            drop_initial_query = "DROP TABLE IF EXISTS {table}"
            if is_cascade:
                drop_initial_query += " CASCADE"
            drop_initial_query += ";"
            drop_query = psycopg2.sql.SQL(drop_initial_query).format(
                table=psycopg2.sql.Identifier(table),
            )
            return drop_query

        query = generate_query()
        if execute:
            self.cursor.execute(query)
            self.conn.commit()

    def create(
        self,
        table: str,
        fields: T.Dict[str, T.Any],
        constraints: T.Dict[str, T.Any] = {},
        is_unlogged=False,
        execute=True,
    ):
        def generate_query():
            create_initial_query = (
                "CREATE UNLOGGED TABLE IF NOT EXISTS {table} (%s, %s);"
            )
            if not is_unlogged:
                create_initial_query = create_initial_query.replace("UNLOGGED ", "")

            stringed_fields = []
            for field in fields:
                field_attributes = fields[field]
                if "type" not in field_attributes:
                    raise Exception(f"Missing type for %s" % field)
                stringed_field = "%s %s%%s" % (field, field_attributes["type"].upper())
                stringed_field = stringed_field % (
                    " NOT NULL"
                    if "is_not_null" in field_attributes
                    and field_attributes["is_not_null"]
                    else ""
                )
                stringed_fields.append(stringed_field)

            based_constraints = {
                "primary_key": "PRIMARY KEY",
                "foreign_key": "FOREIGN KEY",
                "unique": "UNIQUE",
            }
            stringed_constraints = []
            for constraint in constraints:
                constraint_attributes = constraints[constraint]
                if "fields" not in constraint_attributes:
                    raise Exception("Missing fields for %s" % constraint)
                if constraint not in based_constraints:
                    raise Exception(
                        f"Only support {list(based_constraints.keys())} constraints"
                    )

                stringed_constraint = "%s (%s)%%s" % (
                    based_constraints[constraint],
                    ", ".join(constraint_attributes["fields"]),
                )
                if constraint == "foreign_key":
                    if "ref" not in constraint_attributes:
                        raise Exception("Foreign key constraint missing reference")
                    foreign_constraint_attributes = constraint_attributes["ref"]
                    if "table" not in foreign_constraint_attributes:
                        raise Exception(
                            "Foreign key constraint missing reference table"
                        )
                    if "fields" not in foreign_constraint_attributes:
                        raise Exception(
                            "Foreign key constraint missing reference fields"
                        )
                    stringed_constraint = stringed_constraint % (
                        " REFERENCES %s (%s)"
                        % (
                            foreign_constraint_attributes["table"],
                            ", ".join(foreign_constraint_attributes["fields"]),
                        )
                    )
                else:
                    stringed_constraint = stringed_constraint % ""
                stringed_constraints.append(stringed_constraint)
            create_initial_query = create_initial_query % (
                ", ".join(stringed_fields),
                ", ".join(stringed_constraints),
            )
            create_query = psycopg2.sql.SQL(
                modules.general.utilities.clean_text(
                    ["'", '"', "-"], create_initial_query
                )
            )
            create_query = create_query.format(
                table=psycopg2.sql.Identifier(table),
            )
            return create_query

        query = generate_query()
        if execute:
            self.cursor.execute(query)
            self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


def preprocess(champ_data: T.Dict[str, T.Any]):
    output = {**champ_data, "biography": "<br><br>".join(champ_data["biography"])}
    return output

DB_HOST = "127.0.0.1"
DB_USER = "postgres"
DB_PASSWORD = "maylaai2000"
DB_NAME = "loldata"

SCHEMAS = {
    "info": {
        "fields": {
            "id": {"type": "serial", "is_not_null": True},
            "name": {"type": "varchar(30)", "is_not_null": True},
            "race": {"type": "varchar(20)"},
            "type": {"type": "varchar(15)"},
            "region": {"type": "varchar(30)"},
            "quote": {"type": "varchar(200)"},
            "short_biography": {"type": "text"},
            "ref_name": {"type": "varchar(20)", "is_not_null": True},
            "biography": {"type": "text"},
        },
        "constraints": {
            "primary_key": {"fields": ["id"]},
            "unique": {"fields": ["ref_name"]},
        },
    }
}

MAPPINGS = {
    "info": {
        "id": "id",
        "name": "name",
        "race": "race",
        "type": "type",
        "region": "region",
        "quote": "quote",
        "biography_text": "short_biography",
        "ref_name": "ref_name",
        "biography": "biography",
    }
}

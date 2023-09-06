package models

import (
	"database/sql"

	_ "github.com/lib/pq"
)

type Champion struct {
	ID              int            `json:"id"`
	Name            sql.NullString `json:"name"`
	Race            sql.NullString `json:"race"`
	Type            sql.NullString `json:"type"`
	Region          sql.NullString `json:"region"`
	Quote           sql.NullString `json:"quote"`
	Short_Biography sql.NullString `json:"short_biography"`
	Ref_Name        sql.NullString `json:"ref_name"`
	Biography       sql.NullString `json:"biography"`
}

type Champions struct {
	Champions []Champion `json:"champions"`
}

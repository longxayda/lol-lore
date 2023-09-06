package database

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

var Db *sql.DB

const (
	host     = "localhost"
	port     = 5432
	user     = "postgres"
	password = "maylaai2000"
	dbname   = "loldata"
)

var connString = fmt.Sprintf(
	"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
	host, port, user, password, dbname)

func ConnDb() error {
	var err error
	db, err := sql.Open("postgres", connString)
	if err != nil {
		return err
	}
	if err := db.Ping(); err != nil {
		return err
	}
	Db = db
	return nil
}

func CloseDb() error {
	err := Db.Close()
	return err
}

func GetConfig() string {
	return connString
}

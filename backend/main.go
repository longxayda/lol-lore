package main

import (
	"fmt"
	"go-postgres/database"
	"go-postgres/routes"
	"log"

	"github.com/gofiber/fiber/v2"
)

func setUpRoutes(app *fiber.App) {
	app.Get("/", routes.HandleHomepage)
	app.Get("/:name", routes.HandleChampion)
	app.Get("/story/:name", routes.HandleStory)
}

func main() {
	// connect with postgres

	if err := database.ConnDb(); err != nil {
		log.Fatal(err)
	} else {
		fmt.Printf("POSTGRES CONNECTED")
	}
	defer database.CloseDb()
	app := fiber.New()

	setUpRoutes(app)

	//404 handler
	app.Use(func(c *fiber.Ctx) error {
		return c.SendStatus(404)
	})

	log.Fatal(app.Listen(":3000"))
}

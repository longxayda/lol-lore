package routes

import (
	"go-postgres/database"
	"go-postgres/models"

	"github.com/gofiber/fiber/v2"
)

func HandleHomepage(c *fiber.Ctx) error {
	return c.SendString("Homepage handler")
}

func HandleChampion(c *fiber.Ctx) error {
	records, err := database.Db.Query("SELECT name, race, type FROM info ORDER BY id")
	if err != nil {
		return c.Status(500).SendString(err.Error())
	}
	defer records.Close()
	data := models.Champions{}

	for records.Next() {
		champion := models.Champion{}
		err := records.Scan(
			&champion.Name,
			&champion.Race,
			&champion.Type,
		)
		if err != nil {
			return err
		}
		data.Champions = append(data.Champions, champion)
	}
	return c.JSON(data)
}

func HandleStory(c *fiber.Ctx) error {
	return c.SendString("End of Story")
}

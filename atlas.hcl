data "external_schema" "sqlalchemy" {
  program = [
    "atlas-provider-sqlalchemy",
    "--path", "./meme_database",
    "--dialect", "postgresql" // mariadb | postgresql | sqlite | mssql
  ]
}

env "sqlalchemy" {
  src = data.external_schema.sqlalchemy.url
  url = "postgresql://postgres:1234@127.0.0.1:5432/postgres?sslmode=disable"
  dev = "docker+postgres://_/my-postgres-vector:latest/dev?search_path=public"
  migration {
    dir = "file://migrations"
  }
  format {
    migrate {
      diff = "{{ sql . \"  \" }}"
    }
  }
}

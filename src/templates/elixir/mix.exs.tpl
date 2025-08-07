defmodule {{SERVICE_NAME_PASCAL}}.MixProject do
  use Mix.Project

  @version "0.1.0"

  def project do
    [
      app: :{{SERVICE_NAME_UNDERSCORE}},
      version: @version,
      elixir: "~> 1.16",
      elixirc_paths: elixirc_paths(Mix.env()),
      start_permanent: Mix.env() == :prod,
      aliases: aliases(),
      deps: deps(),
      docs: docs(),
      dialyzer: [
        plt_add_apps: [:mix, :ex_unit, :credo],
        ignore_warnings: ".dialyzer_ignore.exs"
      ]
    ]
  end

  # Configuration for the OTP application.
  def application do
    [
      mod: { {{SERVICE_NAME_PASCAL}}.Application, []},
      extra_applications: [:logger, :runtime_tools]
    ]
  end

  # Specifies which paths to compile per environment.
  defp elixirc_paths(:test), do: ["lib", "test/support"]
  defp elixirc_paths(_), do: ["lib"]

  # Specifies your project dependencies.
  defp deps do
    [
      # Phoenix Framework
      {:phoenix, "~> 1.7.0"},
      {:phoenix_ecto, "~> 4.4"},
      {:phoenix_html, "~> 4.0"},
      {:phoenix_live_reload, "~> 1.2", only: :dev},
      {:phoenix_live_view, "~> 0.20.0"},
      {:phoenix_live_dashboard, "~> 0.8"},
      {:phoenix_pubsub, "~> 2.1"},
      {:phoenix_view, "~> 2.0"},
      
      # Database
      {:ecto_sql, "~> 3.9"},
      {:postgrex, ">= 0.0.0"},
      
      # HTTP Client & API
      {:plug_cowboy, "~> 2.7"},
      {:jason, "~> 1.4"},
      {:finch, "~> 0.13"},
      {:tesla, "~> 1.4"},
      
      # Background Jobs
      {:oban, "~> 2.19"},
      
      # Utilities
      {:gettext, "~> 0.20"},
      {:bcrypt_elixir, "~> 3.0"},
      {:cors_plug, "~> 3.0"},
      
      # Monitoring & Telemetry
      {:telemetry, "~> 1.1"},
      {:telemetry_metrics, "~> 1.1"},
      {:telemetry_poller, "~> 1.0"},
      
      # Development Tools
      {:credo, "~> 1.7", only: [:dev, :test], runtime: false},
      {:dialyxir, "~> 1.4", only: [:dev, :test], runtime: false},
      {:ex_doc, "~> 0.34", only: :dev, runtime: false},
      {:sobelow, "~> 0.11", only: :dev},
      
      # Testing
      {:ex_machina, "~> 2.7", only: [:test]},
      {:faker, "~> 0.17", only: [:test]},
      {:bypass, "~> 2.1", only: :test}
    ]
  end

  # Aliases are shortcuts or tasks specific to the current project.
  defp aliases do
    [
      # Project setup
      setup: ["deps.get", "ecto.setup"],
      
      # Database management  
      "ecto.setup": ["ecto.create", "ecto.migrate", "run priv/repo/seeds.exs"],
      "ecto.reset": ["ecto.drop", "ecto.setup"],
      
      # Testing
      test: ["ecto.create --quiet", "ecto.migrate --quiet", "test"],
      
      # Code quality
      check: [
        "compile --all-warnings --warnings-as-errors",
        "credo --strict",
        "format --check-formatted",
        "dialyzer",
        "sobelow --config"
      ],
      
      # Development server
      dev: ["phx.server"],
      
      # Production
      "phx.digest": ["cmd --cd assets npm run build", "phx.digest"]
    ]
  end

  defp docs do
    [
      main: "readme",
      formatters: ["html"],
      extras: ["README.md"]
    ]
  end
end

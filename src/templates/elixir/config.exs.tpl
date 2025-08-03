# This file is responsible for configuring your application
# and its dependencies with the aid of the Config module.
import Config

# General application configuration
config :{{SERVICE_NAME_UNDERSCORE}},
  ecto_repos: [{{SERVICE_NAME_PASCAL}}.Repo],
  generators: [timestamp_type: :utc_datetime]

# Configures the endpoint
config :{{SERVICE_NAME_UNDERSCORE}}, {{SERVICE_NAME_PASCAL}}Web.Endpoint,
  url: [host: "localhost"],
  adapter: Bandit.PhoenixAdapter,
  render_errors: [
    formats: [html: {{SERVICE_NAME_PASCAL}}Web.ErrorHTML, json: {{SERVICE_NAME_PASCAL}}Web.ErrorJSON],
    layout: false
  ],
  pubsub_server: {{SERVICE_NAME_PASCAL}}.PubSub,
  live_view: [signing_salt: "your-signing-salt"]

# Configure esbuild (the version is required)
config :esbuild,
  version: "0.17.11",
  {{SERVICE_NAME_UNDERSCORE}}: [
    args:
      ~w(js/app.js --bundle --target=es2017 --outdir=../priv/static/assets --external:/fonts/* --external:/images/*),
    cd: Path.expand("../assets", __DIR__),
    env: %{"NODE_PATH" => Path.expand("../deps", __DIR__)}
  ]

# Configure tailwind (the version is required)
config :tailwind,
  version: "3.4.0",
  {{SERVICE_NAME_UNDERSCORE}}: [
    args: ~w(
      --config=tailwind.config.js
      --input=css/app.css
      --output=../priv/static/assets/app.css
    ),
    cd: Path.expand("../assets", __DIR__)
  ]

# Configures Elixir's Logger
config :logger, :console,
  format: "$time $metadata[$level] $message\n",
  metadata: [:request_id]

# Use Jason for JSON parsing in Phoenix
config :phoenix, :json_library, Jason

# Configure Oban
config :{{SERVICE_NAME_UNDERSCORE}}, Oban,
  engine: Oban.Engines.Basic,
  queues: [default: 10],
  repo: {{SERVICE_NAME_PASCAL}}.Repo

# Import environment specific config. This must remain at the bottom
# of this file so it overrides the configuration defined above.
import_config "#{config_env()}.exs"
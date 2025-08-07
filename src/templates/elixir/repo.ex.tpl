defmodule {{SERVICE_NAME_PASCAL}}.Repo do
  use Ecto.Repo,
    otp_app: :{{SERVICE_NAME_UNDERSCORE}},
    adapter: Ecto.Adapters.Postgres
end

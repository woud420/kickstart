defmodule {{SERVICE_NAME_PASCAL}}Web.HealthController do
  use {{SERVICE_NAME_PASCAL}}Web, :controller

  def show(conn, _params) do
    json(conn, %{
      status: "healthy",
      service: "{{SERVICE_NAME}}",
      version: "0.1.0",
      timestamp: DateTime.utc_now() |> DateTime.to_iso8601()
    })
  end
end

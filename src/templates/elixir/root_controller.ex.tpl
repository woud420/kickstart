defmodule {{SERVICE_NAME_PASCAL}}Web.RootController do
  use {{SERVICE_NAME_PASCAL}}Web, :controller

  def index(conn, _params) do
    json(conn, %{
      message: "{{SERVICE_NAME}} is running",
      service: "{{SERVICE_NAME}}",
      version: "0.1.0"
    })
  end
end

defmodule {{SERVICE_NAME_PASCAL}}Web.RootControllerTest do
  use {{SERVICE_NAME_PASCAL}}Web.ConnCase, async: true

  describe "GET /api/" do
    test "returns service information", %{conn: conn} do
      conn = get(conn, ~p"/api/")
      
      assert json_response(conn, 200) == %{
        "message" => "{{SERVICE_NAME}} is running",
        "service" => "{{SERVICE_NAME}}",
        "version" => "0.1.0"
      }
    end
  end
end
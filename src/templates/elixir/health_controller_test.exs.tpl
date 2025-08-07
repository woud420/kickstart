defmodule {{SERVICE_NAME_PASCAL}}Web.HealthControllerTest do
  use {{SERVICE_NAME_PASCAL}}Web.ConnCase, async: true

  describe "GET /health" do
    test "returns healthy status", %{conn: conn} do
      conn = get(conn, ~p"/health")
      
      assert json_response(conn, 200) == %{
        "status" => "healthy",
        "service" => "{{SERVICE_NAME}}",
        "version" => "0.1.0",
        "timestamp" => json_response(conn, 200)["timestamp"]
      }
      
      # Ensure timestamp is present and valid ISO8601
      assert is_binary(json_response(conn, 200)["timestamp"])
    end
  end
end

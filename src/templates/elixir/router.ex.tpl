defmodule {{SERVICE_NAME_PASCAL}}Web.Router do
  use {{SERVICE_NAME_PASCAL}}Web, :router

  pipeline :api do
    plug :accepts, ["json"]
  end

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: { {{SERVICE_NAME_PASCAL}}Web.Layouts, :root}
    plug :protect_from_forgery
    plug :put_secure_browser_headers
  end

  # Health endpoint (should be accessible without /api prefix)
  scope "/", {{SERVICE_NAME_PASCAL}}Web do
    pipe_through :api
    
    get "/health", HealthController, :show
  end

  scope "/api", {{SERVICE_NAME_PASCAL}}Web do
    pipe_through :api

    get "/", RootController, :index
  end

  scope "/", {{SERVICE_NAME_PASCAL}}Web do
    pipe_through :browser

    live "/", PageLive, :index
  end

  # Enable LiveDashboard and Swoosh mailbox preview in development
  if Application.compile_env(:{{SERVICE_NAME_UNDERSCORE}}, :dev_routes) do
    import Phoenix.LiveDashboard.Router

    scope "/dev" do
      pipe_through :browser

      live_dashboard "/dashboard", metrics: {{SERVICE_NAME_PASCAL}}Web.Telemetry
    end
  end
end
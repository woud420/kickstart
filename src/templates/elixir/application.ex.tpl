defmodule {{SERVICE_NAME_PASCAL}}.Application do
  @moduledoc false

  use Application

  @impl Application
  def start(_type, _args) do
    children = [
      # Database
      {{SERVICE_NAME_PASCAL}}.Repo,
      
      # PubSub system
      {Phoenix.PubSub, name: {{SERVICE_NAME_PASCAL}}.PubSub},
      
      # HTTP Client
      {Finch, name: {{SERVICE_NAME_PASCAL}}.Finch},
      
      # Background Jobs  
      {Oban, Application.fetch_env!(:{{SERVICE_NAME_UNDERSCORE}}, Oban)},
      
      # Web Endpoint
      {{SERVICE_NAME_PASCAL}}Web.Endpoint
    ]

    opts = [strategy: :one_for_one, name: {{SERVICE_NAME_PASCAL}}.Supervisor]
    Supervisor.start_link(children, opts)
  end

  # Tell Phoenix to update the endpoint configuration
  # whenever the application is updated.
  @impl Application
  def config_change(changed, _new, removed) do
    {{SERVICE_NAME_PASCAL}}Web.Endpoint.config_change(changed, removed)
    :ok
  end
end

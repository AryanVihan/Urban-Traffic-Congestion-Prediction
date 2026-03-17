"""
mcp_servers/
------------
MCP (Model Context Protocol) server suite for the ForgeML Traffic Congestion Predictor.

Four lightweight FastMCP servers expose the project's ML model and analytics
as callable tools and readable resources — usable by any MCP-compatible client
(Claude Desktop, Claude API with tool use, custom agents, etc.).

Servers
-------
prediction_server   Tools: predict_congestion, predict_batch_hours,
                           compute_risk_forecast, get_feature_vector
                    Resources: traffic://model/info, traffic://model/thresholds,
                               traffic://model/feature_importance

analytics_server    Tools: get_hourly_traffic_profile, get_congestion_distribution,
                           get_weather_impact_summary, get_rush_hour_stats,
                           get_segment_risk_for_hour, compare_weekday_vs_weekend
                    Resources: traffic://dataset/summary, traffic://dataset/peak_analysis,
                               traffic://segments/metadata

insights_server     Tools: explain_prediction_for_conditions, get_action_plan,
                           get_system_insights, get_level_description
                    Resources: traffic://insights/system, traffic://insights/level_guide,
                               traffic://insights/rush_schedule

map_server          Tools: get_corridor_congestion_map, get_bottleneck_segments,
                           get_segment_history
                    Resources: traffic://map/segments, traffic://map/bottleneck_factors

bridge              Synchronous bridge used by the Streamlit app — calls core.py
                    functions directly without subprocess overhead.

Usage
-----
Run a server standalone:
    python -m mcp_servers.prediction_server
    python -m mcp_servers.analytics_server
    python -m mcp_servers.insights_server
    python -m mcp_servers.map_server

Use the bridge from Streamlit:
    from mcp_servers.bridge import MCPBridge
    bridge = MCPBridge()
    result = bridge.predict_now()
"""

__version__ = "1.0.0"
__all__ = ["bridge"]

"use client";

import React, { useEffect, useState } from "react";

// Types matching our backend Pydantic schemas
interface PlatformMetric {
  platform: string;
  views: number;
  likes: number;
  clicks: number;
}

interface TrendPoint {
  date: string;
  views: number;
  likes: number;
  clicks: number;
}

export default function AnalyticsDashboard() {
  const [summary, setSummary] = useState({
    total_views: 4520,
    total_likes: 980,
    total_clicks: 410,
    by_platform: [
      { platform: "linkedin", views: 1850, likes: 320, clicks: 120 },
      { platform: "twitter", views: 1420, likes: 450, clicks: 180 },
      { platform: "facebook", views: 540, likes: 90, clicks: 30 },
      { platform: "instagram", views: 710, likes: 120, clicks: 80 }
    ] as PlatformMetric[]
  });

  const [trends, setTrends] = useState<TrendPoint[]>([
    { date: "Mon", views: 420, likes: 80, clicks: 30 },
    { date: "Tue", views: 480, likes: 90, clicks: 35 },
    { date: "Wed", views: 510, likes: 110, clicks: 42 },
    { date: "Thu", views: 460, likes: 95, clicks: 38 },
    { date: "Fri", views: 590, likes: 130, clicks: 52 },
    { date: "Sat", views: 640, likes: 150, clicks: 65 },
    { date: "Sun", views: 710, likes: 160, clicks: 80 }
  ]);

  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"views" | "likes" | "clicks">("views");

  useEffect(() => {
    async function fetchData() {
      try {
        const token = localStorage.getItem("access_token");
        const headers: HeadersInit = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        // Attempt to fetch summary
        const summaryRes = await fetch("http://localhost:8080/api/v1/analytics/summary", { headers });
        if (summaryRes.ok) {
          const summaryData = await summaryRes.json();
          setSummary(summaryData);
        }

        // Attempt to fetch trends
        const trendsRes = await fetch("http://localhost:8080/api/v1/analytics/trends", { headers });
        if (trendsRes.ok) {
          const trendsData = await trendsRes.json();
          if (trendsData.trends && trendsData.trends.length > 0) {
            setTrends(trendsData.trends);
          }
        }
      } catch (err) {
        console.warn("Could not connect to live backend API. Using pre-seeded mock analytics data.", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // Calculate coordinates for responsive SVG Line Chart
  const svgWidth = 500;
  const svgHeight = 200;
  const padding = 20;

  const dataValues = trends.map(t => t[activeTab]);
  const maxVal = Math.max(...dataValues, 10);
  const minVal = Math.min(...dataValues, 0);
  const valRange = maxVal - minVal;

  const points = trends.map((t, i) => {
    const x = padding + (i / (trends.length - 1)) * (svgWidth - padding * 2);
    // Invert Y coordinate because SVG (0,0) is top-left
    const y = svgHeight - padding - ((t[activeTab] - minVal) / valRange) * (svgHeight - padding * 2);
    return { x, y, ...t };
  });

  const polylinePoints = points.map(p => `${p.x},${p.y}`).join(" ");

  // Color mapping based on active metric tab
  const activeColor = {
    views: "stroke-emerald-400 fill-emerald-400/10 stroke-width-3",
    likes: "stroke-pink-400 fill-pink-400/10 stroke-width-3",
    clicks: "stroke-sky-400 fill-sky-400/10 stroke-width-3"
  }[activeTab];

  const gradientColor = {
    views: "from-emerald-400/20 to-transparent",
    likes: "from-pink-400/20 to-transparent",
    clicks: "from-sky-400/20 to-transparent"
  }[activeTab];

  // Helper for brand colors
  const getBrandColor = (platform: string) => {
    switch (platform) {
      case "linkedin": return "bg-blue-600";
      case "twitter": return "bg-sky-400";
      case "facebook": return "bg-indigo-600";
      case "instagram": return "bg-pink-500";
      default: return "bg-gray-400";
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 to-indigo-400 bg-clip-text text-transparent">
              Analytics Dashboard
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Monitor your AI-driven social media campaign metrics and conversion data.
            </p>
          </div>
          {loading && (
            <span className="text-xs px-2.5 py-1 rounded-full border border-teal-500/30 bg-teal-500/10 text-teal-400 animate-pulse">
              Syncing API...
            </span>
          )}
        </div>

        {/* Core KPI metrics grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Card: Total Views */}
          <div 
            onClick={() => setActiveTab("views")}
            className={`cursor-pointer group p-6 rounded-2xl border transition-all duration-300 ${
              activeTab === "views" 
                ? "border-emerald-500 bg-slate-900/80 shadow-lg shadow-emerald-500/10 scale-102"
                : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
            }`}
          >
            <div className="flex justify-between items-center text-slate-400 text-sm">
              <span>Total Views</span>
              <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full text-xs font-semibold">
                +14.2%
              </span>
            </div>
            <div className="text-3xl font-black mt-2 text-slate-50">{summary.total_views.toLocaleString()}</div>
            <div className="text-xs text-slate-500 mt-1">Active campaign views</div>
          </div>

          {/* Card: Total Likes */}
          <div 
            onClick={() => setActiveTab("likes")}
            className={`cursor-pointer group p-6 rounded-2xl border transition-all duration-300 ${
              activeTab === "likes" 
                ? "border-pink-500 bg-slate-900/80 shadow-lg shadow-pink-500/10 scale-102"
                : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
            }`}
          >
            <div className="flex justify-between items-center text-slate-400 text-sm">
              <span>Total Likes</span>
              <span className="text-pink-400 bg-pink-500/10 px-2 py-0.5 rounded-full text-xs font-semibold">
                +8.7%
              </span>
            </div>
            <div className="text-3xl font-black mt-2 text-slate-50">{summary.total_likes.toLocaleString()}</div>
            <div className="text-xs text-slate-500 mt-1">Interactions & reactions</div>
          </div>

          {/* Card: Total Clicks */}
          <div 
            onClick={() => setActiveTab("clicks")}
            className={`cursor-pointer group p-6 rounded-2xl border transition-all duration-300 ${
              activeTab === "clicks" 
                ? "border-sky-500 bg-slate-900/80 shadow-lg shadow-sky-500/10 scale-102"
                : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
            }`}
          >
            <div className="flex justify-between items-center text-slate-400 text-sm">
              <span>Total Link Clicks</span>
              <span className="text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded-full text-xs font-semibold">
                +22.1%
              </span>
            </div>
            <div className="text-3xl font-black mt-2 text-slate-50">{summary.total_clicks.toLocaleString()}</div>
            <div className="text-xs text-slate-500 mt-1">Direct conversion traffic</div>
          </div>
        </div>

        {/* Charts & Breakdown Split */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Timeseries SVG Line Chart */}
          <div className="lg:col-span-2 p-6 rounded-2xl border border-slate-800 bg-slate-900/30 flex flex-col justify-between">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 capitalize">
                <span>{activeTab} Performance Trend</span>
              </h2>
              <div className="text-xs text-slate-400 bg-slate-800/60 px-3 py-1 rounded-lg">
                Last 7 Days
              </div>
            </div>

            {/* Custom SVG Drawing */}
            <div className="relative w-full h-[200px]">
              <svg 
                viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
                className="w-full h-full overflow-visible"
              >
                <defs>
                  <linearGradient id="chart-area-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" className="stop-color" />
                    <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* Grid guidelines */}
                <line x1={padding} y1={padding} x2={svgWidth - padding} y2={padding} stroke="#1e293b" strokeDasharray="3 3" />
                <line x1={padding} y1={svgHeight / 2} x2={svgWidth - padding} y2={svgHeight / 2} stroke="#1e293b" strokeDasharray="3 3" />
                <line x1={padding} y1={svgHeight - padding} x2={svgWidth - padding} y2={svgHeight - padding} stroke="#334155" />

                {/* Shaded Area fill under line */}
                <path
                  d={`M ${points[0].x} ${svgHeight - padding} L ${polylinePoints} L ${points[points.length - 1].x} ${svgHeight - padding} Z`}
                  className={`${gradientColor} fill-current`}
                />

                {/* Trend line */}
                <polyline
                  fill="none"
                  className={activeColor}
                  strokeWidth="3.5"
                  points={polylinePoints}
                />

                {/* Interaction points */}
                {points.map((p, i) => (
                  <g key={i} className="group/dot">
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r="4"
                      className="fill-slate-950 stroke-2 cursor-pointer transition-all duration-150 hover:r-6"
                      stroke={
                        activeTab === "views" ? "#34d399" : activeTab === "likes" ? "#f472b6" : "#38bdf8"
                      }
                    />
                    {/* Tooltip labels */}
                    <text
                      x={p.x}
                      y={p.y - 12}
                      textAnchor="middle"
                      className="text-[9px] font-bold fill-slate-300 opacity-0 group-hover/dot:opacity-100 transition-opacity duration-150 bg-slate-950"
                    >
                      {p[activeTab]}
                    </text>
                  </g>
                ))}
              </svg>
            </div>

            {/* X-axis labels */}
            <div className="flex justify-between px-5 text-xs text-slate-500 font-semibold mt-4">
              {trends.map((t, idx) => (
                <span key={idx}>{t.date}</span>
              ))}
            </div>
          </div>

          {/* Platform Performance progress bars */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/30 flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-100 mb-6">
                Platform Breakdown
              </h2>
              <div className="space-y-5">
                {summary.by_platform.map((p, idx) => {
                  const maxPlatformVal = Math.max(...summary.by_platform.map(item => item[activeTab]), 1);
                  const percentage = (p[activeTab] / maxPlatformVal) * 100;

                  return (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex justify-between items-center text-xs">
                        <span className="capitalize font-semibold text-slate-300 flex items-center gap-1.5">
                          <span className={`w-2.5 h-2.5 rounded-full ${getBrandColor(p.platform)}`}></span>
                          {p.platform}
                        </span>
                        <span className="text-slate-400 font-bold">
                          {p[activeTab].toLocaleString()} <span className="text-[10px] text-slate-600 capitalize">{activeTab}</span>
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800/80 overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-1000 ${getBrandColor(p.platform)}`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            <div className="text-xs text-slate-600 mt-6 pt-4 border-t border-slate-800/60">
              Aggregated from visual webhook listeners.
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Settings, 
  Layers, 
  HelpCircle, 
  Users, 
  Radio,
  BarChart3,
  Search,
  Tag,
  Bot
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Meetings Library", icon: LayoutDashboard, path: "/", active: pathname === "/" },
    { name: "Live Assistant", icon: Radio, path: "#", active: false, badge: "Coming Soon" },
    { name: "Smart Search", icon: Search, path: "#", active: false, badge: "Coming Soon" },
    { name: "AskFred AI Chat", icon: Bot, path: "#", active: false, badge: "Coming Soon" },
    { name: "Analytics", icon: BarChart3, path: "#", active: false, badge: "Coming Soon" },
    { name: "Topic Tracker", icon: Tag, path: "#", active: false, badge: "Coming Soon" },
    { name: "Integrations", icon: Layers, path: "#", active: false, badge: "Coming Soon" },
    { name: "Team Spaces", icon: Users, path: "#", active: false, badge: "Coming Soon" },
    { name: "Settings", icon: Settings, path: "#", active: false, badge: "Placeholder" },
  ];

  return (
    <div className="sidebar" id="sidebar-nav">
      <div className="logo">
        <div style={{
          width: "28px",
          height: "28px",
          borderRadius: "8px",
          background: "linear-gradient(135deg, #7c3aed, #ec4899)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontWeight: "bold",
          fontSize: "14px"
        }}>
          FF
        </div>
        <span className="logo-text">fireflies.ai</span>
      </div>

      <ul className="nav-list">
        {navItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <li key={idx}>
              {item.path !== "#" ? (
                <Link href={item.path} className={`nav-item ${item.active ? "active" : ""}`}>
                  <Icon size={18} />
                  <span>{item.name}</span>
                </Link>
              ) : (
                <div className="nav-item" style={{ cursor: "not-allowed", opacity: 0.75 }}>
                  <Icon size={18} />
                  <span style={{ flexGrow: 1 }}>{item.name}</span>
                  {item.badge && (
                    <span style={{
                      fontSize: "10px",
                      background: "rgba(124, 58, 237, 0.1)",
                      color: "#a855f7",
                      padding: "2px 6px",
                      borderRadius: "10px",
                      fontWeight: 600
                    }}>
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>

      <div className="sidebar-footer">
        <div className="user-avatar">RB</div>
        <div className="user-info">
          <span className="user-name">Raju Bhagat</span>
          <span className="user-role">SDE Fullstack</span>
        </div>
      </div>
    </div>
  );
}

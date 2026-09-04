import { useEffect, useState } from "react";
import { supabase } from "./lib/supabaseClient";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./App.css";

function App() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvents();
  }, []);

  async function fetchEvents() {
    const { data, error } = await supabase
      .from("audit_log")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) {
      console.error("Supabase error:", error);
    } else {
      setEvents(data || []);
    }

    setLoading(false);
  }

  // Count unique payments that actually failed
  const failedPaymentIds = new Set(
    events
      .filter(
        (event) =>
          event.event_type === "payment_failed" ||
          event.event_type === "failure_detected"
      )
      .map((event) => event.payment_id)
      .filter(Boolean)
  );

  const failures = failedPaymentIds.size;

  // A payment is considered recovered only when the executor
  // reports a successful recovery outcome.
  const recoveredPaymentIds = new Set(
    events
      .filter((event) => event.event_type === "recovery_completed")
      .filter((event) => {
        const status = event.data?.outcome?.status;

        return [
          "payment_recovered",
          "retry_success",
          "payment_link_paid",
        ].includes(status);
      })
      .map((event) => event.payment_id)
      .filter(Boolean)
  );

  const recovered = recoveredPaymentIds.size;

  const recoveryRate =
    failures > 0 ? Math.round((recovered / failures) * 100) : 0;

  // Show actual recovery actions instead of every audit event
  const actionCounts = {};

  events
    .filter((event) => event.event_type === "recovery_completed")
    .forEach((event) => {
      const action = event.data?.final_action_taken || "Unknown";

      actionCounts[action] = (actionCounts[action] || 0) + 1;
    });

  const chartData = Object.entries(actionCounts).map(
    ([action, count]) => ({
      action,
      count,
    })
  );

  return (
    <div className="dashboard">
      <header className="topbar">
        <div>
          <h1>RecoverAI</h1>
          <p>AI-Powered Revenue Recovery</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          System Online
        </div>
      </header>

      <main className="content">
        <section className="hero">
          <div>
            <h2>Revenue Recovery Command Center</h2>
            <p>
              Monitor failed payments, AI recommendations, policy decisions,
              and recovery actions.
            </p>
          </div>
        </section>

        <section className="metrics">
          <div className="metric-card">
            <span>Failed Payments</span>
            <strong>{failures}</strong>
            <small>Unique failed payments</small>
          </div>

          <div className="metric-card">
            <span>Recovery Rate</span>
            <strong>{recoveryRate}%</strong>
            <small>Successful recoveries</small>
          </div>

          <div className="metric-card">
            <span>Recovered</span>
            <strong>{recovered}</strong>
            <small>Payments recovered</small>
          </div>
        </section>

        <section className="grid">
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Recovery Actions</h3>
                <p>Final actions approved by the policy engine</p>
              </div>
            </div>

            <div className="chart">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="action" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty">
                  No recovery actions recorded yet.
                </div>
              )}
            </div>
          </div>

          <div className="panel safety-panel">
            <h3>AI Safety Layer</h3>

            <div className="safety-item">
              <span>🤖</span>
              <div>
                <strong>LLM proposes</strong>
                <p>Gemini recommends a recovery action.</p>
              </div>
            </div>

            <div className="arrow">↓</div>

            <div className="safety-item">
              <span>🛡️</span>
              <div>
                <strong>Policy validates</strong>
                <p>Rules check whether the action is allowed.</p>
              </div>
            </div>

            <div className="arrow">↓</div>

            <div className="safety-item">
              <span>⚡</span>
              <div>
                <strong>Executor acts</strong>
                <p>Only approved actions reach Razorpay.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="panel audit-panel">
          <div className="panel-header">
            <div>
              <h3>Audit Trail</h3>
              <p>Every recovery decision is recorded</p>
            </div>
          </div>

          {loading ? (
            <div className="empty">Loading audit events...</div>
          ) : events.length === 0 ? (
            <div className="empty">
              No audit events yet. Run a payment failure test to populate
              this table.
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Payment ID</th>
                    <th>AI Proposed</th>
                    <th>Final Action</th>
                    <th>Time</th>
                  </tr>
                </thead>

                <tbody>
                  {events.slice(0, 10).map((event) => {
                    const proposed =
                      event.data?.llm_proposed_action ||
                      event.data?.proposed_action ||
                      "-";

                    const finalAction =
                      event.data?.final_action_taken ||
                      event.data?.action ||
                      "-";

                    const overridden =
                      proposed !== "-" &&
                      finalAction !== "-" &&
                      proposed !== finalAction;

                    return (
                      <tr key={event.id}>
                        <td>
                          <span className="event-badge">
                            {event.event_type}
                          </span>
                        </td>

                        <td>{event.payment_id || "-"}</td>

                        <td>{proposed}</td>

                        <td>
                          <span
                            className={
                              overridden
                                ? "override-badge"
                                : "action-badge"
                            }
                          >
                            {finalAction}
                            {overridden && " • OVERRIDDEN"}
                          </span>
                        </td>

                        <td>
                          {new Date(event.created_at).toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
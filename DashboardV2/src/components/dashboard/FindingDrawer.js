import React, { useState, useRef, useEffect } from 'react';
import { X, ThumbsUp, ThumbsDown, Send, ExternalLink, RefreshCw, Clock } from 'lucide-react';
import SeverityBadge from '../common/SeverityBadge';
import { formatCvss, formatEpss, formatAiScore, formatRelative, capitalize } from '../../utils/formatters';
import { useChat } from '../../hooks/useChat';
import { FINDING_STATUS_COLORS } from '../../utils/constants';
import toast from 'react-hot-toast';

const TABS = ['Details', 'AI Analysis', 'LLM Assistant', 'Jira', 'History'];

// ---- Details tab ----
function DetailsTab({ finding }) {
  return (
    <div className="space-y-4 text-sm">
      <div>
        <p className="text-xs font-semibold text-text-muted uppercase mb-1">Description</p>
        <p className="text-text-secondary leading-relaxed">{finding.title} — this finding was detected by {finding.scanner} during the most recent security scan. Immediate remediation is recommended based on the AI risk assessment.</p>
      </div>
      {finding.file_path && (
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase mb-1">Affected Location</p>
          <code className="font-mono text-xs bg-bg-tertiary px-3 py-2 rounded block text-text-primary">{finding.file_path}</code>
        </div>
      )}
      {finding.cve_id && (
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase mb-1">CVE ID</p>
          <a href={`https://nvd.nist.gov/vuln/detail/${finding.cve_id}`} target="_blank" rel="noreferrer" className="font-mono text-sm text-accent hover:underline flex items-center gap-1">
            {finding.cve_id} <ExternalLink size={12} />
          </a>
        </div>
      )}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase mb-1">CVSS Score</p>
          <p className="font-mono text-lg font-bold text-text-primary">{formatCvss(finding.cvss)}</p>
        </div>
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase mb-1">EPSS Score</p>
          <p className="font-mono text-lg font-bold text-text-primary">{formatEpss(finding.epss)}</p>
        </div>
      </div>
      <div>
        <p className="text-xs font-semibold text-text-muted uppercase mb-1">Remediation Guidance</p>
        <div className="bg-success-light border border-green-200 rounded-md p-3 text-success text-xs leading-relaxed">
          Update the affected library to the latest patched version and validate all user inputs before processing. Apply parameterized queries to prevent injection attacks.
        </div>
      </div>
    </div>
  );
}

// ---- AI Analysis tab ----
function AiAnalysisTab({ finding }) {
  const score = finding.ai_score || 5;
  const color = score >= 7 ? '#DC2626' : score >= 4 ? '#D97706' : '#16A34A';
  const factors = [
    { label: 'EPSS Score', value: 0.88 },
    { label: 'Exploit Available', value: 0.75 },
    { label: 'CVSS Score', value: 0.68 },
    { label: 'Asset Criticality', value: 0.55 },
    { label: 'Scanner Confidence', value: 0.42 },
  ];
  return (
    <div className="space-y-5 text-sm">
      <div className="text-center py-4">
        <p className="text-xs text-text-muted mb-2">AI Risk Score</p>
        <div className="relative w-32 h-32 mx-auto">
          <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#E2E8F0" strokeWidth="12" />
            <circle
              cx="60" cy="60" r="50" fill="none"
              stroke={color} strokeWidth="12"
              strokeDasharray={`${(score / 10) * 314} 314`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold" style={{ color }}>{score.toFixed(1)}</span>
            <span className="text-xs text-text-muted">/10</span>
          </div>
        </div>
      </div>
      <div>
        <p className="text-xs font-semibold text-text-muted uppercase mb-2">Risk Factors</p>
        <div className="space-y-2">
          {factors.map((f) => (
            <div key={f.label}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="text-text-secondary">{f.label}</span>
                <span className="font-medium text-text-primary">{(f.value * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
                <div className="h-full bg-critical rounded-full" style={{ width: `${f.value * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-warning-light border border-yellow-200 rounded-md p-3 text-xs text-text-secondary">
        <strong className="text-text-primary">AI Assessment: </strong>
        CVSS rates this {finding.severity} ({formatCvss(finding.cvss)}) — AI model scores this {formatAiScore(finding.ai_score)} due to high EPSS ({formatEpss(finding.epss)}) and confirmed exploit availability in the wild.
      </div>
      <div>
        <p className="text-xs text-text-muted">Model confidence: <strong className="text-text-primary">94.2%</strong></p>
      </div>
    </div>
  );
}

// ---- LLM Assistant tab ----
function LlmAssistantTab({ finding }) {
  const context = { findingId: finding.id };
  const { messages, isTyping, error, sendMessage, retry } = useChat(context);
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const quickActions = [
    'Explain this vulnerability',
    'Suggest a fix',
    'Generate PoC impact summary',
    'Write Jira ticket description',
  ];

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-wrap gap-2 mb-3">
        {quickActions.map((action) => (
          <button
            key={action}
            onClick={() => sendMessage(action)}
            className="px-3 py-1.5 text-xs font-medium bg-accent-light text-accent rounded-md hover:bg-blue-100 transition-colors"
          >
            {action}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 min-h-0" style={{ maxHeight: '280px' }}>
        {messages.length === 0 && (
          <p className="text-xs text-text-muted text-center py-6">Ask anything about this finding…</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] text-xs rounded-lg px-3 py-2 leading-relaxed ${m.role === 'user' ? 'bg-accent text-white' : 'bg-white border border-border text-text-primary shadow-sm'}`}>
              {m.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white border border-border rounded-lg px-3 py-2 flex gap-1">
              {[0, 1, 2].map((i) => (
                <span key={i} className="w-1.5 h-1.5 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 text-xs text-danger">
            {error}
            <button onClick={retry} className="underline">Retry</button>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Ask about this finding…"
          className="flex-1 h-9 px-3 border border-border rounded-md text-xs outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
        />
        <button onClick={handleSend} disabled={!input.trim() || isTyping} className="h-9 px-3 bg-accent text-white rounded-md disabled:opacity-50 hover:bg-accent-hover transition-colors">
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}

// ---- Jira drawer tab ----
function JiraDrawerTab({ finding }) {
  const [created, setCreated] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1200));
    setLoading(false);
    setCreated(true);
    toast.success('Jira ticket SEC-143 created successfully!');
  };

  if (created) {
    return (
      <div className="bg-success-light border border-green-200 rounded-md p-4">
        <p className="text-sm font-semibold text-success mb-1">Ticket Created: <span className="font-mono">SEC-143</span></p>
        <p className="text-xs text-text-secondary">Status: Open · Last sync: just now</p>
        <div className="flex gap-2 mt-3">
          <button className="flex items-center gap-1 text-xs text-accent hover:underline"><ExternalLink size={12} /> Open in Jira</button>
          <button className="flex items-center gap-1 text-xs text-text-secondary hover:text-text-primary"><RefreshCw size={12} /> Sync Status</button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-text-secondary">No Jira ticket linked to this finding yet.</p>
      <div className="space-y-2 text-sm">
        <div>
          <label className="block text-xs font-medium text-text-primary mb-1">Project Key</label>
          <input defaultValue="SEC" className="w-full h-9 px-3 border border-border rounded-md text-sm font-mono outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent" />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-primary mb-1">Issue Type</label>
          <select className="w-full h-9 px-3 border border-border rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent">
            <option>Bug</option>
            <option>Security</option>
            <option>Task</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-text-primary mb-1">Summary</label>
          <input defaultValue={finding.title} className="w-full h-9 px-3 border border-border rounded-md text-sm outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent" />
        </div>
      </div>
      <button onClick={handleCreate} disabled={loading} className="w-full h-9 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-md transition-colors disabled:opacity-60">
        {loading ? 'Creating ticket…' : 'Create Jira Ticket'}
      </button>
    </div>
  );
}

// ---- History tab ----
function HistoryTab({ finding }) {
  const events = [
    { type: 'created', label: 'Finding detected by ' + finding.scanner, time: finding.date },
    { type: 'ai', label: 'AI risk score assigned: ' + formatAiScore(finding.ai_score), time: finding.date },
    { type: 'status', label: 'Status changed to: ' + capitalize(finding.status), time: finding.date },
  ];
  return (
    <div className="space-y-3">
      {events.map((e, i) => (
        <div key={i} className="flex gap-3">
          <div className="flex flex-col items-center">
            <div className="w-2 h-2 rounded-full bg-accent mt-1 flex-shrink-0" />
            {i < events.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
          </div>
          <div className="pb-3">
            <p className="text-sm text-text-primary">{e.label}</p>
            <p className="text-xs text-text-muted flex items-center gap-1 mt-0.5"><Clock size={11} />{formatRelative(e.time)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---- Main Drawer ----
export default function FindingDrawer({ finding, onClose }) {
  const [activeTab, setActiveTab] = useState('Details');
  const [feedback, setFeedback] = useState(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackSent, setFeedbackSent] = useState(false);

  if (!finding) return null;

  const statusColors = FINDING_STATUS_COLORS[finding.status] || { bg: 'bg-bg-tertiary', text: 'text-text-muted' };

  const handleFeedback = (vote) => {
    setFeedback(vote);
    setTimeout(() => {
      setFeedbackSent(true);
      toast.success('Feedback submitted. Thank you!');
    }, 600);
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/25 z-40" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-full max-w-[560px] bg-white shadow-lg z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-start gap-3 px-5 py-4 border-b border-border">
          <div className="flex-1 min-w-0">
            <h2 className="font-semibold text-text-primary text-base leading-snug line-clamp-2">{finding.title}</h2>
            <div className="flex items-center gap-2 mt-1">
              <SeverityBadge severity={finding.severity} />
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors.bg} ${statusColors.text}`}>
                {finding.status === 'in_progress' ? 'In Progress' : capitalize(finding.status)}
              </span>
              <span className="text-xs text-text-muted">{finding.scanner}</span>
              <span className="text-xs text-text-muted">· {formatRelative(finding.date)}</span>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-bg-secondary text-text-muted flex-shrink-0">
            <X size={18} />
          </button>
        </div>

        {/* Inner tabs */}
        <div className="flex border-b border-border px-5">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab
                  ? 'border-accent text-accent'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto px-5 py-5">
          {activeTab === 'Details' && <DetailsTab finding={finding} />}
          {activeTab === 'AI Analysis' && <AiAnalysisTab finding={finding} />}
          {activeTab === 'LLM Assistant' && <LlmAssistantTab finding={finding} />}
          {activeTab === 'Jira' && <JiraDrawerTab finding={finding} />}
          {activeTab === 'History' && <HistoryTab finding={finding} />}
        </div>

        {/* Feedback panel — always visible */}
        <div className="border-t border-border px-5 py-4 bg-bg-secondary">
          {feedbackSent ? (
            <p className="text-sm text-success font-medium">✓ Thanks for your feedback!</p>
          ) : (
            <div>
              <p className="text-sm font-medium text-text-primary mb-2">Was this finding correctly prioritized by AI?</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleFeedback('yes')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    feedback === 'yes' ? 'bg-success text-white' : 'bg-white border border-border text-text-secondary hover:bg-success-light hover:text-success'
                  }`}
                >
                  <ThumbsUp size={14} /> Yes
                </button>
                <button
                  onClick={() => handleFeedback('no')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    feedback === 'no' ? 'bg-danger text-white' : 'bg-white border border-border text-text-secondary hover:bg-danger-light hover:text-danger'
                  }`}
                >
                  <ThumbsDown size={14} /> No
                </button>
                {feedback && (
                  <input
                    value={feedbackComment}
                    onChange={(e) => setFeedbackComment(e.target.value)}
                    placeholder="Optional comment…"
                    className="flex-1 h-8 px-2 border border-border rounded-md text-xs outline-none"
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

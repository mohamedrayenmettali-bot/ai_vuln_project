import React, { useState } from 'react';
import { RefreshCw, Brain } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts';
import ConfirmModal from '../common/ConfirmModal';
import toast from 'react-hot-toast';

const modelInfo = {
  version: 'v2.4.1',
  trained_on: '2024-01-10',
  dataset_size: 48320,
};

const metrics = [
  { label: 'Accuracy', value: '94.2%', color: '#16A34A' },
  { label: 'Precision', value: '91.8%', color: '#2563EB' },
  { label: 'Recall', value: '93.5%', color: '#D97706' },
  { label: 'F1-Score', value: '92.6%', color: '#7C3AED' },
];

const featureImportance = [
  { feature: 'EPSS Score', importance: 0.28 },
  { feature: 'CVSS Score', importance: 0.22 },
  { feature: 'Exploit Available', importance: 0.18 },
  { feature: 'Scanner Confidence', importance: 0.12 },
  { feature: 'Asset Criticality', importance: 0.09 },
  { feature: 'Age (days)', importance: 0.05 },
  { feature: 'Exposure (internet)', importance: 0.04 },
  { feature: 'CVE Age', importance: 0.02 },
];

const trainingHistory = Array.from({ length: 20 }, (_, i) => ({
  epoch: i + 1,
  accuracy: 0.7 + (i / 20) * 0.25 + (Math.random() * 0.02 - 0.01),
  loss: 0.8 - (i / 20) * 0.65 + (Math.random() * 0.02),
}));

const confusionMatrix = {
  tp: 3821, fp: 298,
  fn: 247, tn: 12934,
};

export default function AiModelTab() {
  const [showRetrain, setShowRetrain] = useState(false);
  const [retraining, setRetraining] = useState(false);

  const handleRetrain = async () => {
    setRetraining(true);
    setShowRetrain(false);
    await new Promise((r) => setTimeout(r, 2000));
    setRetraining(false);
    toast.success('Model retraining started. You will be notified when complete.');
  };

  return (
    <div className="space-y-6">
      {/* Model info header */}
      <div className="bg-white border border-border rounded-lg shadow-md p-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-critical-light rounded-lg flex items-center justify-center">
            <Brain size={24} className="text-critical" />
          </div>
          <div>
            <p className="font-semibold text-text-primary">AI Risk Scoring Model</p>
            <div className="flex items-center gap-3 text-xs text-text-muted mt-0.5">
              <span>Version: <strong className="text-text-secondary font-mono">{modelInfo.version}</strong></span>
              <span>Trained: <strong className="text-text-secondary">{modelInfo.trained_on}</strong></span>
              <span>Dataset: <strong className="text-text-secondary">{modelInfo.dataset_size.toLocaleString()} findings</strong></span>
            </div>
          </div>
        </div>
        <button
          onClick={() => setShowRetrain(true)}
          disabled={retraining}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-critical hover:bg-purple-700 rounded-md transition-colors disabled:opacity-60"
        >
          <RefreshCw size={14} className={retraining ? 'animate-spin' : ''} />
          {retraining ? 'Retraining…' : 'Retrain Model'}
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="bg-white border border-border rounded-lg shadow-md p-5 text-center">
            <p className="text-sm text-text-muted mb-2">{m.label}</p>
            <p className="text-3xl font-bold" style={{ color: m.color }}>{m.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion matrix */}
        <div className="bg-white border border-border rounded-lg shadow-md p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Confusion Matrix</h3>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'True Positive', value: confusionMatrix.tp, bg: 'bg-success-light', text: 'text-success' },
              { label: 'False Positive', value: confusionMatrix.fp, bg: 'bg-warning-light', text: 'text-warning' },
              { label: 'False Negative', value: confusionMatrix.fn, bg: 'bg-danger-light', text: 'text-danger' },
              { label: 'True Negative', value: confusionMatrix.tn, bg: 'bg-success-light', text: 'text-success' },
            ].map((c) => (
              <div key={c.label} className={`${c.bg} rounded-lg p-4 text-center`}>
                <p className={`text-2xl font-bold ${c.text}`}>{c.value.toLocaleString()}</p>
                <p className="text-xs text-text-secondary mt-1">{c.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Feature importance */}
        <div className="bg-white border border-border rounded-lg shadow-md p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Feature Importance</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={featureImportance} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <YAxis type="category" dataKey="feature" tick={{ fontSize: 10, fill: '#475569' }} width={110} />
              <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
              <Bar dataKey="importance" fill="#7C3AED" radius={[0, 4, 4, 0]} name="Importance" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Training history */}
      <div className="bg-white border border-border rounded-lg shadow-md p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4">Training History</h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={trainingHistory}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis dataKey="epoch" tick={{ fontSize: 11, fill: '#94A3B8' }} label={{ value: 'Epoch', position: 'insideBottom', offset: -3, fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
            <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="accuracy" stroke="#16A34A" strokeWidth={2} dot={false} name="Accuracy" />
            <Line type="monotone" dataKey="loss" stroke="#DC2626" strokeWidth={2} dot={false} name="Loss" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <ConfirmModal
        isOpen={showRetrain}
        onClose={() => setShowRetrain(false)}
        onConfirm={handleRetrain}
        title="Retrain AI Model"
        message="This will start a background retraining job using all available labeled findings. Training typically takes 10-30 minutes. The current model will remain active until retraining is complete."
        confirmLabel="Start Retraining"
        loading={retraining}
      />
    </div>
  );
}

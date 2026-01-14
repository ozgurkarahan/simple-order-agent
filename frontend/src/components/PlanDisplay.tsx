/**
 * PlanDisplay Component
 *
 * Displays an execution plan with phases and tasks in a checklist format.
 * Shows status icons: ✓ (completed), ⏳ (in progress), ⏸️ (pending)
 */

import React from 'react';

export interface TaskItem {
  id: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  error?: string;
}

export interface Phase {
  id: string;
  name: string;
  description?: string;
  tasks: TaskItem[];
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
}

export interface Plan {
  id: string;
  description: string;
  phases: Phase[];
  createdAt: string;
  approvedAt?: string;
}

interface PlanDisplayProps {
  plan: Plan;
  isExecuting?: boolean;
  onApprove?: () => void;
  onReject?: (feedback: string) => void;
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
  showApprovalButtons?: boolean;
  showExecutionControls?: boolean;
  isPaused?: boolean;
}

const getStatusIcon = (status: string): string => {
  switch (status) {
    case 'completed':
      return '✓';
    case 'in_progress':
      return '⏳';
    case 'failed':
      return '❌';
    case 'skipped':
      return '⏭️';
    case 'pending':
    default:
      return '⏸️';
  }
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'text-green-600';
    case 'in_progress':
      return 'text-blue-600';
    case 'failed':
      return 'text-red-600';
    case 'skipped':
      return 'text-gray-400';
    case 'pending':
    default:
      return 'text-gray-400';
  }
};

export const PlanDisplay: React.FC<PlanDisplayProps> = ({
  plan,
  isExecuting = false,
  onApprove,
  onReject,
  onPause,
  onResume,
  onCancel,
  showApprovalButtons = false,
  showExecutionControls = false,
  isPaused = false,
}) => {
  const [rejectFeedback, setRejectFeedback] = React.useState('');
  const [showRejectInput, setShowRejectInput] = React.useState(false);

  const handleReject = () => {
    if (rejectFeedback.trim() && onReject) {
      onReject(rejectFeedback.trim());
      setRejectFeedback('');
      setShowRejectInput(false);
    }
  };

  return (
    <div className="mb-4 rounded-lg border-2 border-blue-200 bg-blue-50/50 p-4">
      {/* Header */}
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-blue-900">Execution Plan</h3>
        <p className="text-sm text-gray-600 mt-1">{plan.description}</p>
      </div>

      {/* Plan Content */}
      <div className="space-y-3">
        {plan.phases.map((phase, phaseIndex) => (
          <div key={phase.id} className="space-y-2">
            {/* Phase Header */}
            <div className="flex items-start gap-2">
              <span className={`text-lg font-medium ${getStatusColor(phase.status)}`}>
                {getStatusIcon(phase.status)}
              </span>
              <div className="flex-1">
                <div className="font-semibold text-gray-900">
                  {phaseIndex + 1}. {phase.name}
                </div>
                {phase.description && (
                  <div className="text-sm text-gray-600">{phase.description}</div>
                )}
              </div>
            </div>

            {/* Tasks */}
            <div className="ml-8 space-y-1.5">
              {phase.tasks.map((task) => (
                <div key={task.id} className="flex items-start gap-2">
                  <span className={`text-base ${getStatusColor(task.status)}`}>
                    {getStatusIcon(task.status)}
                  </span>
                  <div className="flex-1">
                    <span className="text-sm text-gray-700">{task.description}</span>
                    {task.error && (
                      <div className="text-xs text-red-600 mt-0.5">Error: {task.error}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Status Badge */}
      {isExecuting && (
        <div className="mt-4 pt-3 border-t border-blue-200">
          <div className="flex items-center gap-2 text-sm text-blue-700">
            <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full"></div>
            <span>Executing plan...</span>
          </div>
        </div>
      )}

      {/* Approval Buttons */}
      {showApprovalButtons && (
        <div className="mt-4 pt-3 border-t border-blue-200">
          {!showRejectInput ? (
            <div className="flex gap-2">
              <button
                onClick={onApprove}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
              >
                Approve Plan
              </button>
              <button
                onClick={() => setShowRejectInput(true)}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium"
              >
                Reject Plan
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <textarea
                value={rejectFeedback}
                onChange={(e) => setRejectFeedback(e.target.value)}
                placeholder="Please provide feedback on why you're rejecting this plan..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                rows={3}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleReject}
                  disabled={!rejectFeedback.trim()}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  Submit Feedback
                </button>
                <button
                  onClick={() => {
                    setShowRejectInput(false);
                    setRejectFeedback('');
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Execution Controls */}
      {showExecutionControls && (
        <div className="mt-4 pt-3 border-t border-blue-200">
          <div className="flex gap-2">
            {!isPaused ? (
              <button
                onClick={onPause}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors font-medium"
              >
                Pause
              </button>
            ) : (
              <button
                onClick={onResume}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
              >
                Resume
              </button>
            )}
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlanDisplay;

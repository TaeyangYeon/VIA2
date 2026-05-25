import { useEffect, useRef } from 'react';
import { Play, Square, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  setExecution,
  setExecutionId,
  setExecutionStatus,
} from '../../store/slices/executionSlice';
import { setResult } from '../../store/slices/resultSlice';
import { startExecution, cancelExecution, getExecution } from '../../services/api';

export default function ExecutionPanel() {
  const dispatch = useAppDispatch();
  const execution = useAppSelector(s => s.execution);
  const imageCount = useAppSelector(s => s.images.analysis.length);
  const config = useAppSelector(s => s.config);

  const { status, execution_id, current_agent, current_iteration, goal_validation, progress } =
    execution;

  const maxIteration = config.max_iteration;
  const isRunning = status === 'running';
  const canStart = status === 'idle' || status === 'completed' || status === 'failed' || status === 'cancelled';
  const hasImages = imageCount > 0;

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Polling
  useEffect(() => {
    if (!execution_id || !isRunning) return;

    intervalRef.current = setInterval(async () => {
      try {
        const data = await getExecution(execution_id);
        const mappedStatus =
          data.status === 'pending' ? 'running' : (data.status as 'running' | 'completed' | 'failed' | 'cancelled');

        dispatch(
          setExecution({
            status: mappedStatus,
            current_agent: data.current_agent,
            current_iteration: data.current_iteration,
            goal_validation: data.goal_validation,
            progress: data.progress,
          })
        );

        if (data.result) {
          dispatch(setResult(data.result));
        }

        if (
          data.status === 'completed' ||
          data.status === 'failed' ||
          data.status === 'cancelled'
        ) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch {
        // network error — keep polling
      }
    }, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [execution_id, isRunning, dispatch]);

  const handleStart = async () => {
    try {
      dispatch(setExecutionStatus('running'));
      const res = await startExecution({ user_text: '' });
      dispatch(setExecutionId(res.execution_id));
    } catch {
      dispatch(setExecutionStatus('failed'));
    }
  };

  const handleStop = async () => {
    if (!execution_id) return;
    try {
      await cancelExecution(execution_id);
      dispatch(setExecutionStatus('cancelled'));
    } catch {
      // ignore
    }
  };

  return (
    <div data-testid="execution-panel" className="h-full overflow-y-auto p-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Play size={20} className="text-text-secondary" />
        <h2 className="text-base font-semibold text-text-primary">Execution</h2>
      </div>

      {/* Status display */}
      <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-4">
        {/* Idle */}
        {status === 'idle' && (
          <p className="text-sm text-text-secondary">Ready to execute</p>
        )}

        {/* Running — agent progress */}
        {isRunning && (
          <div className="flex flex-col gap-3">
            {/* Agent name with pulsing dot */}
            <div data-testid="current-agent-display" className="flex items-center gap-2">
              <span
                className="w-2 h-2 rounded-full bg-white animate-pulse flex-shrink-0"
                style={{ background: '#a3a3a3' }}
              />
              <span className="text-sm text-text-primary font-medium">
                {current_agent ?? 'Initializing…'}
              </span>
            </div>

            {/* Iteration counter */}
            <div data-testid="iteration-counter" className="text-xs text-text-secondary">
              Iteration {current_iteration} / {maxIteration}
            </div>

            {/* Progress bar */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-xs text-text-disabled">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div
                  data-testid="progress-bar"
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${progress}%`, background: '#a3a3a3' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Completed */}
        {status === 'completed' && (
          <div
            data-testid="status-completed"
            className="flex items-center gap-2"
            style={{ color: '#4ade80' }}
          >
            <CheckCircle size={16} />
            <span className="text-sm font-medium">Execution completed</span>
          </div>
        )}

        {/* Failed */}
        {status === 'failed' && (
          <div
            data-testid="status-failed"
            className="flex items-center gap-2"
            style={{ color: '#f87171' }}
          >
            <XCircle size={16} />
            <span className="text-sm font-medium">Execution failed</span>
          </div>
        )}

        {/* Cancelled */}
        {status === 'cancelled' && (
          <div
            data-testid="status-cancelled"
            className="flex items-center gap-2 text-text-secondary"
          >
            <XCircle size={16} />
            <span className="text-sm font-medium">Execution cancelled</span>
          </div>
        )}
      </div>

      {/* Goal validation warnings */}
      {goal_validation && goal_validation.warnings.length > 0 && (
        <div
          data-testid="goal-validation-warnings"
          className="flex flex-col gap-2 p-3 rounded-lg border"
          style={{
            background: 'rgba(250,204,21,0.08)',
            borderColor: 'rgba(250,204,21,0.3)',
          }}
        >
          {goal_validation.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2" style={{ color: '#facc15' }}>
              <AlertTriangle size={13} className="flex-shrink-0 mt-0.5" />
              <span className="text-xs">{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        {canStart && (
          <button
            data-testid="start-btn"
            onClick={handleStart}
            disabled={!hasImages}
            className="flex items-center gap-2 px-4 py-2 rounded bg-white/10 border border-white/15 text-sm text-text-primary hover:bg-white/15 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play size={14} />
            <span>{status === 'failed' ? 'Retry' : status === 'completed' || status === 'cancelled' ? 'Run Again' : 'Start'}</span>
          </button>
        )}

        {isRunning && (
          <button
            data-testid="stop-btn"
            onClick={handleStop}
            className="flex items-center gap-2 px-4 py-2 rounded bg-white/5 border border-white/10 text-sm text-text-secondary hover:bg-white/8 hover:text-text-primary transition-all duration-150"
          >
            <Square size={14} />
            <span>Stop</span>
          </button>
        )}
      </div>

      {/* No images warning */}
      {canStart && !hasImages && (
        <p className="text-xs text-text-disabled">
          Upload analysis images before starting execution.
        </p>
      )}

      {/* Running indicator in header area */}
      {isRunning && (
        <div className="flex items-center gap-2 text-xs text-text-disabled">
          <Loader2 size={12} className="animate-spin" />
          <span>Processing…</span>
        </div>
      )}
    </div>
  );
}

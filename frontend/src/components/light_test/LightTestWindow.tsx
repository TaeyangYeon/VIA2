import { ChangeEvent, DragEvent, useRef, useState } from 'react';
import { Monitor, Upload, X } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  setLightTestImage,
  setAnalysisLoading,
  setAnalysisResult,
  setAnalysisError,
  clearAnalysis,
} from '../../store/slices/lightTestSlice';
import { uploadImage } from '../../services/api';
import { analyzeLightTestImage } from '../../services/light_test_api';
import DualViewLayout from './DualViewLayout';

type UploadStatus = 'idle' | 'loading' | 'error';

const ACCEPT_TYPES = ['image/png', 'image/jpeg', 'image/bmp', 'image/tiff'];
const ACCEPT_EXTS = /\.(png|jpe?g|bmp|tiff?)$/i;

export default function LightTestWindow() {
  const dispatch = useAppDispatch();
  const image = useAppSelector(s => s.light_test.image);
  const analysis_status = useAppSelector(s => s.light_test.analysis_status);
  const analysis_error = useAppSelector(s => s.light_test.analysis_error);
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!ACCEPT_TYPES.includes(file.type) && !ACCEPT_EXTS.test(file.name)) {
      setErrorMsg('Unsupported file type. Please use PNG, JPG, BMP, or TIFF.');
      setStatus('error');
      return;
    }
    setStatus('loading');
    setErrorMsg(null);
    try {
      const metadata = await uploadImage(file);
      dispatch(setLightTestImage(metadata));
      setStatus('idle');

      dispatch(setAnalysisLoading());
      try {
        const response = await analyzeLightTestImage(file);
        dispatch(
          setAnalysisResult({
            depth: response.depth,
            material: response.material,
            status: response.status,
          }),
        );
      } catch (err) {
        dispatch(
          setAnalysisError(err instanceof Error ? err.message : 'Analysis failed'),
        );
      }
    } catch {
      setErrorMsg('Upload failed. Please try again.');
      setStatus('error');
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleRemove = () => {
    dispatch(setLightTestImage(null));
    dispatch(clearAnalysis());
    setStatus('idle');
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const dismissError = () => {
    setStatus('idle');
    setErrorMsg(null);
  };

  return (
    <div
      data-testid="light-test-window"
      className="flex flex-col h-screen w-screen overflow-hidden"
      style={{ background: '#0a0a0a' }}
    >
      {/* Header */}
      <header
        data-testid="light-test-header"
        className="flex items-center gap-3 px-6 py-3 flex-shrink-0"
        style={{
          borderBottom: '1px solid #2a2a2a',
          background: 'rgba(17,17,17,0.85)',
          backdropFilter: 'blur(12px)',
        }}
      >
        <Monitor size={16} style={{ color: '#a0a0a0' }} />
        <span className="text-sm font-semibold tracking-wide" style={{ color: '#f5f5f5' }}>
          VIA2 — Light Test
        </span>
        <div
          className="ml-auto flex items-center gap-2 px-2 py-0.5 rounded"
          style={{ background: 'rgba(255,255,255,0.05)' }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: image ? '#4ade80' : '#555555' }}
          />
          <span className="text-xs" style={{ color: '#a0a0a0' }}>
            {image ? 'Image Ready' : 'No Image'}
          </span>
        </div>
      </header>

      {/* Upload area */}
      <div
        className="flex-shrink-0 px-6 py-4"
        style={{ borderBottom: '1px solid #2a2a2a' }}
      >
        {/* Hidden file input — always present */}
        <input
          data-testid="lt-file-input"
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.bmp,.tiff,.tif"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {/* Loading state */}
        {status === 'loading' && (
          <div
            data-testid="lt-loading-state"
            className="flex items-center gap-3 px-4 py-4 rounded-lg"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid #2a2a2a' }}
          >
            <div
              className="w-4 h-4 rounded-full border-2 animate-spin flex-shrink-0"
              style={{ borderColor: '#2a2a2a', borderTopColor: '#a0a0a0' }}
            />
            <span className="text-sm" style={{ color: '#a0a0a0' }}>Uploading image…</span>
          </div>
        )}

        {/* Error state */}
        {status === 'error' && (
          <div
            data-testid="lt-error-state"
            className="flex items-center gap-3 px-4 py-3 rounded-lg"
            style={{
              background: 'rgba(248,113,113,0.05)',
              border: '1px solid rgba(248,113,113,0.2)',
            }}
          >
            <X size={14} style={{ color: '#f87171', flexShrink: 0 }} />
            <span className="text-sm flex-1" style={{ color: '#f87171' }}>
              {errorMsg ?? 'Upload failed'}
            </span>
            <button
              className="text-xs underline transition-all duration-150 flex-shrink-0"
              style={{ color: '#a0a0a0' }}
              onClick={dismissError}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Drop zone — shown when idle and no image */}
        {status === 'idle' && !image && (
          <>
            <div
              data-testid="lt-drop-zone"
              className="rounded-lg cursor-pointer transition-all duration-150"
              style={{
                border: `2px dashed ${isDragging ? '#555555' : '#2a2a2a'}`,
                background: isDragging ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.02)',
              }}
              onDrop={handleDrop}
              onDragOver={(e: DragEvent<HTMLDivElement>) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onClick={() => fileInputRef.current?.click()}
            >
              <div
                data-testid="lt-empty-state"
                className="flex flex-col items-center gap-2 px-4 py-6"
              >
                <Upload size={24} style={{ color: '#555555' }} />
                <p className="text-sm" style={{ color: '#a0a0a0' }}>
                  Drop an image here or click to browse
                </p>
                <p className="text-xs" style={{ color: '#555555' }}>
                  PNG, JPG, BMP, TIFF — any filename accepted
                </p>
              </div>
            </div>
            <div className="flex justify-end mt-2">
              <button
                data-testid="lt-browse-btn"
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-all duration-150"
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid #2a2a2a',
                  color: '#a0a0a0',
                }}
              >
                <Upload size={12} />
                Browse Files
              </button>
            </div>
          </>
        )}

        {/* Image thumbnail */}
        {image && (
          <div
            data-testid="lt-image-thumbnail"
            className="flex items-center gap-3 px-4 py-3 rounded-lg"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid #2a2a2a' }}
          >
            <div
              className="w-10 h-10 rounded flex-shrink-0 overflow-hidden flex items-center justify-center"
              style={{ background: '#1a1a1a', border: '1px solid #2a2a2a' }}
            >
              <img
                src={`http://localhost:8000${image.file_path}`}
                alt={image.original_filename}
                className="w-full h-full object-cover"
                onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: '#f5f5f5' }}>
                {image.original_filename}
              </p>
              <p className="text-xs" style={{ color: '#555555' }}>
                {(image.file_size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              data-testid="lt-remove-btn"
              onClick={handleRemove}
              className="flex-shrink-0 p-1 rounded transition-all duration-150 hover:bg-white/5"
              style={{ color: '#555555' }}
              aria-label="Remove image"
            >
              <X size={14} />
            </button>
          </div>
        )}

        {/* Analysis status indicators */}
        {image && analysis_status === 'loading' && (
          <div
            data-testid="lt-analysis-loading"
            className="flex items-center gap-2 mt-2 px-4 py-2 rounded"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid #2a2a2a' }}
          >
            <div
              className="w-3 h-3 rounded-full border-2 animate-spin flex-shrink-0"
              style={{ borderColor: '#2a2a2a', borderTopColor: '#a0a0a0' }}
            />
            <span className="text-xs" style={{ color: '#a0a0a0' }}>
              Analyzing depth &amp; material…
            </span>
          </div>
        )}

        {image && (analysis_status === 'success' || analysis_status === 'partial') && (
          <div
            data-testid="lt-analysis-complete"
            className="flex items-center gap-2 mt-2 px-4 py-2 rounded"
            style={{
              background: 'rgba(74,222,128,0.05)',
              border: '1px solid rgba(74,222,128,0.2)',
            }}
          >
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ background: '#4ade80' }}
            />
            <span className="text-xs" style={{ color: '#4ade80' }}>
              {analysis_status === 'success' ? 'Analysis complete' : 'Analysis partial'}
            </span>
          </div>
        )}

        {image && analysis_status === 'error' && (
          <div
            data-testid="lt-analysis-error"
            className="flex items-center gap-2 mt-2 px-4 py-2 rounded"
            style={{
              background: 'rgba(248,113,113,0.05)',
              border: '1px solid rgba(248,113,113,0.2)',
            }}
          >
            <X size={12} style={{ color: '#f87171', flexShrink: 0 }} />
            <span className="text-xs" style={{ color: '#f87171' }}>
              {analysis_error ?? 'Analysis failed'}
            </span>
          </div>
        )}
      </div>

      {/* Dual view — shown only when image is loaded */}
      {image && (
        <div className="flex-1 overflow-hidden">
          <DualViewLayout />
        </div>
      )}
    </div>
  );
}

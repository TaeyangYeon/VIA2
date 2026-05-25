import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { Upload, X, Trash2, Image as ImageIcon, AlertCircle, Loader2, FolderOpen } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { addImage, removeImage, clearImages, setAnalysisImages } from '../../store/slices/imagesSlice';
import { uploadImage, getImages, deleteImage, clearAllImages } from '../../services/api';
import type { ImageMetadata } from '../../services/types';

const VALID_FILENAME = /^(ok|ng)_[1-9]\d*\.(png|jpg|jpeg|bmp|tiff)$/i;
const ACCEPTED_TYPES = 'image/png,image/jpeg,image/bmp,image/tiff';

export default function InputPanel() {
  const dispatch = useAppDispatch();
  const analysisImages = useAppSelector(s => s.images.analysis);
  const testImages = useAppSelector(s => s.images.test);
  const images = useMemo(() => [...analysisImages, ...testImages], [analysisImages, testImages]);

  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);

  useEffect(() => {
    getImages()
      .then(imgs => dispatch(setAnalysisImages(imgs)))
      .catch(() => {});
  }, [dispatch]);

  const validateFile = (file: File): string | null => {
    if (!VALID_FILENAME.test(file.name)) {
      return `"${file.name}" is invalid. Expected format: OK_N.ext or NG_N.ext (N ≥ 1, e.g. OK_1.png, NG_3.jpg)`;
    }
    return null;
  };

  const processFiles = useCallback(async (files: FileList | File[]) => {
    setValidationError(null);
    setUploadError(null);

    const fileArr = Array.from(files);
    for (const file of fileArr) {
      const err = validateFile(file);
      if (err) {
        setValidationError(err);
        return;
      }
    }

    setIsUploading(true);
    try {
      for (const file of fileArr) {
        const meta = await uploadImage(file);
        dispatch(addImage(meta));
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Upload failed';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  }, [dispatch]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
    e.target.value = '';
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current += 1;
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      dragCounter.current = 0;
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current = 0;
    setIsDragging(false);
    const { files } = e.dataTransfer;
    if (files && files.length > 0) {
      await processFiles(files);
    }
  };

  const handleDelete = async (img: ImageMetadata) => {
    try {
      await deleteImage(img.id);
      dispatch(removeImage(img.id));
    } catch {
      setUploadError('Failed to delete image');
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllImages();
      dispatch(clearImages());
    } catch {
      setUploadError('Failed to clear images');
    }
  };

  const okCount = images.filter(i => i.label.toUpperCase() === 'OK').length;
  const ngCount = images.filter(i => i.label.toUpperCase() === 'NG').length;
  const hasImages = images.length > 0;

  return (
    <div
      data-testid="input-panel"
      className="flex flex-col h-full gap-4 p-4 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <ImageIcon size={16} className="text-text-secondary" />
          <h2 className="text-sm font-semibold text-text-primary tracking-wide uppercase">
            Input Images
          </h2>
        </div>
        {hasImages && (
          <div className="flex items-center gap-2">
            <span data-testid="count-summary" className="text-xs text-text-secondary font-mono">
              <span className="text-accent-success">OK: {okCount}</span>
              <span className="mx-1 text-text-disabled">/</span>
              <span className="text-accent-error">NG: {ngCount}</span>
            </span>
            <button
              data-testid="clear-all-btn"
              onClick={handleClearAll}
              className="flex items-center gap-1 px-2 py-1 text-xs text-text-secondary hover:text-accent-error border border-border-default hover:border-accent-error rounded transition-all duration-150"
            >
              <Trash2 size={12} />
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Drop Zone */}
      <div
        data-testid="drop-zone"
        data-dragging={isDragging}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative flex flex-col items-center justify-center gap-2 flex-shrink-0
          min-h-[100px] rounded-lg border-2 border-dashed cursor-pointer
          transition-all duration-150
          ${isDragging
            ? 'border-accent-action bg-white/10 scale-[1.01]'
            : 'border-border-accent hover:border-text-disabled bg-white/5 hover:bg-white/[0.07]'
          }
        `}
      >
        <input
          ref={fileInputRef}
          data-testid="file-input"
          type="file"
          accept={ACCEPTED_TYPES}
          multiple
          onChange={handleFileChange}
          className="hidden"
          style={{ display: 'none' }}
        />
        {isDragging ? (
          <>
            <FolderOpen size={24} className="text-accent-action" />
            <p className="text-sm font-medium text-accent-action">Drop files here</p>
          </>
        ) : (
          <>
            <Upload size={20} className="text-text-disabled" />
            <p className="text-xs text-text-secondary text-center leading-relaxed">
              Drop images here or{' '}
              <span className="text-text-primary underline underline-offset-2">browse</span>
            </p>
            <p className="text-xs text-text-disabled font-mono">OK_N.ext · NG_N.ext</p>
          </>
        )}
      </div>

      {/* Validation error */}
      {validationError && (
        <div
          data-testid="validation-error"
          className="flex items-start gap-2 px-3 py-2 rounded-md bg-accent-error/10 border border-accent-error/30 flex-shrink-0"
        >
          <AlertCircle size={14} className="text-accent-error mt-0.5 flex-shrink-0" />
          <p className="text-xs text-accent-error leading-relaxed">{validationError}</p>
        </div>
      )}

      {/* Upload loading */}
      {isUploading && (
        <div
          data-testid="upload-loading"
          className="flex items-center gap-2 px-3 py-2 rounded-md bg-accent-info/10 border border-accent-info/30 flex-shrink-0"
        >
          <Loader2 size={14} className="text-accent-info animate-spin" />
          <p className="text-xs text-accent-info">Uploading…</p>
        </div>
      )}

      {/* Upload error */}
      {uploadError && (
        <div
          data-testid="upload-error"
          className="flex items-start gap-2 px-3 py-2 rounded-md bg-accent-error/10 border border-accent-error/30 flex-shrink-0"
        >
          <AlertCircle size={14} className="text-accent-error mt-0.5 flex-shrink-0" />
          <p className="text-xs text-accent-error">{uploadError}</p>
        </div>
      )}

      {/* Empty state / image grid */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {!hasImages ? (
          <div
            data-testid="empty-state"
            className="flex flex-col items-center justify-center h-full gap-3 py-8"
          >
            <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center">
              <ImageIcon size={20} className="text-text-disabled" />
            </div>
            <div className="text-center">
              <p className="text-sm text-text-secondary">No images uploaded</p>
              <p className="text-xs text-text-disabled mt-1">
                Files must be named OK_N or NG_N (N ≥ 1)
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {images.map(img => (
              <Thumbnail key={img.id} image={img} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface ThumbnailProps {
  image: ImageMetadata;
  onDelete: (img: ImageMetadata) => void;
}

function Thumbnail({ image, onDelete }: ThumbnailProps) {
  const isOk = image.label.toUpperCase() === 'OK';

  return (
    <div
      data-testid={`thumbnail-${image.id}`}
      className="group relative glass-card rounded-md overflow-hidden transition-all duration-150 hover:border-border-accent"
    >
      {/* Preview area */}
      <div className="w-full aspect-square bg-white/5 flex items-center justify-center overflow-hidden">
        <ImageIcon size={24} className="text-text-disabled" />
      </div>

      {/* Info bar */}
      <div className="px-1.5 py-1 flex items-center gap-1">
        <span
          data-testid={`label-${image.id}`}
          className={`text-[10px] font-bold font-mono px-1 rounded ${
            isOk ? 'text-accent-success bg-accent-success/10' : 'text-accent-error bg-accent-error/10'
          }`}
        >
          {image.label.toUpperCase()}
        </span>
        <span className="text-[10px] text-text-secondary truncate flex-1 font-mono">
          {image.original_filename}
        </span>
      </div>

      {/* Delete button */}
      <button
        data-testid={`delete-${image.id}`}
        onClick={() => onDelete(image)}
        className="absolute top-1 right-1 w-5 h-5 rounded bg-bg-top/80 border border-border-default flex items-center justify-center opacity-0 group-hover:opacity-100 hover:border-accent-error hover:text-accent-error transition-all duration-150"
        aria-label={`Delete ${image.original_filename}`}
      >
        <X size={10} />
      </button>
    </div>
  );
}

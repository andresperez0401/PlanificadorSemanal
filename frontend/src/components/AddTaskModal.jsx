import { useState, useEffect, useRef } from 'react';
import '../styles/modal.css';

const tags = ['Trabajo', 'Personal', 'Descanso', 'Estudio', 'Salud'];
const tagColors = {
  Trabajo: '#4CAF50',
  Personal: '#2196F3',
  Descanso: '#FFC107',
  Estudio: '#9C27B0',
  Salud: '#F44336'
};

export default function AddTaskModal({ isOpen, onClose, onSave, defaultDate }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('10:00');
  const [tag, setTag] = useState(tags[0]);
  const [imageFile, setImageFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  
  const fileInputRef = useRef();
  const modalContentRef = useRef();

  // Calculamos "hoy" en formato YYYY-MM-DD
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm   = String(now.getMonth() + 1).padStart(2, '0');
  const dd   = String(now.getDate()).padStart(2, '0');
  const todayStr = `${yyyy}-${mm}-${dd}`;

  // Calculamos la hora actual en HH:MM
  const nowTime = now.toTimeString().slice(0, 5);

  // Resetear campos al abrir el modal
  useEffect(() => {
    if (isOpen) {
      setTitle('');
      setDescription('');
      setDate(defaultDate ? defaultDate.split('T')[0] : todayStr);
      setStartTime('09:00');
      setEndTime('10:00');
      setTag(tags[0]);
      setImageFile(null);
      setPreviewUrl('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      
      // Restablecer scroll al abrir
      if (modalContentRef.current) {
        modalContentRef.current.scrollTop = 0;
      }
    }
  }, [isOpen, defaultDate, todayStr]);

  // Manejar cambios en el tiempo
  useEffect(() => {
    if (date === todayStr && startTime < nowTime) {
      setStartTime(nowTime);
    }

    if (date === todayStr && endTime <= addMinutes(startTime, 60)) {
      setEndTime(addMinutes(startTime, 60));
    }

    if (endTime <= addMinutes(startTime, 60)) {
      setEndTime(addMinutes(startTime, 60));
    }
  }, [date, nowTime, startTime, endTime, todayStr]);

  const uploadToCloudinary = async (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_preset', import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET);
    
    try {
      const response = await fetch(
        `https://api.cloudinary.com/v1_1/${import.meta.env.VITE_CLOUDINARY_CLOUD_NAME}/image/upload`,
        { method: 'POST', body: formData }
      );
      
      const data = await response.json();
      setUploading(false);
      return data.secure_url;
    } catch (error) {
      console.error('Error uploading image:', error);
      setUploading(false);
      return null;
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
        
        // Scroll automático a la imagen después de seleccionar
        setTimeout(() => {
          if (modalContentRef.current) {
            modalContentRef.current.scrollTop = modalContentRef.current.scrollHeight;
          }
        }, 100);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setImageFile(null);
    setPreviewUrl('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title || !date || !startTime || !endTime) return;

    let imageUrl = '';
    if (imageFile) {
      imageUrl = await uploadToCloudinary(imageFile);
      if (!imageUrl) return;
    }

    onSave({ 
      title, 
      description,
      date, 
      startTime, 
      endTime, 
      tag,
      imageUrl 
    });
  };

  // Funcion para sumar minutos
  function addMinutes(timeStr, minsToAdd) {
    const [h, m] = timeStr.split(':').map(Number);
    const date = new Date();
    date.setHours(h);
    date.setMinutes(m + minsToAdd);

    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  }

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h2 className="modal-title">Nueva Tarea</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        
        <form 
          onSubmit={handleSubmit} 
          className="modal-form"
          ref={modalContentRef}
        >
          <div className="form-group">
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Título de la tarea"
              className="modal-input"
              required
            />
          </div>
          
          <div className="form-group">
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Descripción (opcional)"
              className="modal-input"
              rows="3"
            />
          </div>
          
          <div className="form-group">
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              className="modal-input"
              min={todayStr} 
              required
            />
          </div>
          
          <div className="time-group">
            <div className="form-group">
              <label>Inicio</label>
              <input
                type="time"
                value={startTime}
                onChange={e => setStartTime(e.target.value)}
                className="modal-input"
                required
              />
            </div>
            
            <div className="form-group">
              <label>Fin</label>
              <input
                type="time"
                value={endTime}
                onChange={e => setEndTime(e.target.value)}
                className="modal-input"
                required
              />
            </div>
          </div>
          
          <div className="form-group">
            <label>Etiqueta</label>
            <div className="tag-container">
              {tags.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`tag-btn ${tag === t ? 'active' : ''}`}
                  onClick={() => setTag(t)}
                  style={{ 
                    backgroundColor: tag === t ? tagColors[t] : '#f0f0f0',
                    color: tag === t ? 'white' : '#333'
                  }}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          
          <div className="form-group">
            <label>Imagen (opcional)</label>
            <div className="image-upload-container">
              {previewUrl ? (
                <div className="image-preview-wrapper">
                  <img src={previewUrl} alt="Preview" className="image-preview" />
                  <button 
                    type="button" 
                    className="remove-image-btn"
                    onClick={removeImage}
                  >
                    &times;
                  </button>
                </div>
              ) : (
                <div 
                  className="upload-area" 
                  onClick={() => fileInputRef.current.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="file-input"
                    onChange={handleImageChange}
                    style={{ display: 'none' }}
                  />
                  <span className="upload-icon">+</span>
                  <p className="upload-text">Haz clic para subir una imagen</p>
                </div>
              )}
              {uploading && (
                <div className="uploading-overlay">
                  <div className="spinner"></div>
                  <p>Subiendo imagen...</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={onClose} disabled={uploading}>
              Cancelar
            </button>
            <button type="submit" className="save-btn" disabled={uploading}>
              {uploading ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
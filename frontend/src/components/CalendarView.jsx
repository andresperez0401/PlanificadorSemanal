import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import '../styles/calendar.css';

export default function CalendarView({ events, onDateClick, onEventClick }) {
  const renderEventContent = (eventInfo) => {
    const tag = eventInfo.event.extendedProps.tag;
    return (
      <div className="fc-event-content">
        <div className="fc-event-tag">{tag}</div>
        <div className="fc-event-title">{eventInfo.event.title}</div>
        <div className="fc-event-time">
          {eventInfo.timeText}
        </div>
      </div>
    );
  };

  return (
    <div className="calendar-wrapper">
      <FullCalendar
        plugins={[timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        slotMinTime="06:00:00"
        slotMaxTime="22:00:00"
        events={events}
        dateClick={onDateClick}
        eventClick={onEventClick}
        height="auto"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'timeGridDay,timeGridWeek'
        }}
        buttonText={{
          today: 'Hoy',
          week: 'Semana',
          day: 'Día'
        }}
        allDaySlot={false}
        locale="es"
        dayHeaderFormat={{ weekday: 'short', day: 'numeric' }}
        slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
        eventContent={renderEventContent}
      />
    </div>
  );
}
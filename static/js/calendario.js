document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    // Lógica para visualização mobile vs. desktop
    const isMobile = window.innerWidth < 768;
    const initialView = isMobile ? 'timeGridDay' : 'dayGridMonth';

    var calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'pt-br',
        initialView: initialView,
        height: '100%', // Ocupa 100% da altura do contêiner
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridDay,listWeek'
        },
        buttonText: {
            today: 'Hoje',
            month: 'Mês',
            week: 'Semana',
            day: 'Dia',
            list: 'Lista'
        },
        nowIndicator: true,
        editable: true,
        events: '/api/agendamentos',
        eventDrop: function(info) {
            const eventoMovido = {
                id: info.event.id,
                start: info.event.start.toISOString()
            };
            
            fetch('/api/agendamento/mover', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(eventoMovido),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status !== 'sucesso') {
                    info.revert(); 
                    alert("Não foi possível salvar a alteração.");
                }
            })
            .catch(() => {
                info.revert();
                alert("Erro de conexão ao salvar a alteração.");
            });
        }
    });

    calendar.render();
});
function loadChart(labels, data) {
    const ctx = document.getElementById('myChart').getContext( '2D');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Math Marks',
                data: math
            },
            {
                label: 'Science Marks',
                data: science
            },
            {
                label: 'English Marks',
                data: english
            }]
        }
    });
}
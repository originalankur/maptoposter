document.getElementById('radius').addEventListener('input', e => document.getElementById('radiusVal').textContent = Math.round(e.target.value / 1000));

document.getElementById('mapForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('generateBtn');
    const loader = document.getElementById('loader');
    const img = document.getElementById('resultImage');
    const link = document.getElementById('downloadLink');
    const err = document.getElementById('errorMsg');

    btn.disabled = true; loader.classList.remove('hidden');
    img.classList.add('hidden'); link.classList.add('hidden'); err.textContent = '';

    try {
        const res = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                city: document.getElementById('city').value,
                country: document.getElementById('country').value,
                theme: document.getElementById('theme').value,
                radius: document.getElementById('radius').value
            })
        });
        const data = await res.json();

        if (data.success) {
            img.src = `/posters/${data.filename}`; img.classList.remove('hidden');
            link.href = `/posters/${data.filename}`; link.download = data.filename; link.classList.remove('hidden');
            loader.classList.add('hidden');
        } else {
            throw new Error(data.error);
        }
    } catch (e) {
        err.textContent = e.message || "Connection error.";
        loader.classList.add('hidden');
    } finally {
        btn.disabled = false;
    }
});
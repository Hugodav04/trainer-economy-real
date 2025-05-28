function buscar() {
    const marca = document.getElementById('marca').value;
    const modelo = document.getElementById('modelo').value;
    const talla = document.getElementById('talla').value;
    
    if (!marca || !modelo || !talla) {
        alert("Por favor, complete todos los campos antes de buscar.");
        return;
    }

    alert(`Buscando: Marca: ${marca}, Modelo: ${modelo}, Talla: ${talla}`);
}

function comprar() {
    alert('Redirigiendo a la página de compra...');
}
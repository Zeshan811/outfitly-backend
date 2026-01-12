const url = "http://127.0.0.1:5000/books";
async function addbook() {
    let data = {}
    let na = document.getElementById("name").value
    let aut = document.getElementById("author").value
    let pri = document.getElementById("price").value
    if (na.length > 0 && aut.length > 0 && pri.length > 0) {
        data = { "name": na, "author": aut, "price": pri };
        let response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });
        let result = await response.json();
        document.getElementById("div").innerText = JSON.stringify(result, null, 2);

    }

    else {
        document.getElementById("div").innerText = "Kindly add details"
    }
}
async function updatebook() {
    let data = {};
    let na = document.getElementById("na").value;
    let aut = document.getElementById("aut").value;
    let pri = document.getElementById("pri").value;
    let id = document.getElementById("id").value;
    data = { "id": id, "name": na, "author": aut, "price": pri };
    let response = await fetch(url, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
    let result = await response.json();
    document.getElementById("div").innerText = JSON.stringify(result, null, 2);

}
async function Getallbooks() {
    let response = await fetch(url, {
        method: "GET"
    });
    let result = await response.json();
    document.getElementById("div").innerText = JSON.stringify(result, null, 2);

}
async function delbook() {
    let id = document.getElementById("del").value
    let response = await fetch(url, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ "id": id })
    });
    let result = await response.json();
    document.getElementById("div").innerText = JSON.stringify(result, null, 2);

}
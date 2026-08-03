"use strict";

const POLL_INTERVAL_MS = 1000;


// -------------------------------
// Leaflet地図
// -------------------------------

let map = null;

let currentMarker = null;


// 現在計測中の軌跡
let trackLine = null;

let trackPoints = [];


// CSV軌跡
let csvTrackLine = null;


const el = {

    currentTime:
        document.getElementById("current-time"),

    runningState:
        document.getElementById("running-state"),

    message:
        document.getElementById("message"),


    gpsFix:
        document.getElementById("gps-fix"),

    latitude:
        document.getElementById("latitude"),

    longitude:
        document.getElementById("longitude"),


    temperature:
        document.getElementById("temperature"),


    records:
        document.getElementById("records"),

    filename:
        document.getElementById("filename"),


    connectionStatus:
        document.getElementById("connection-status"),


    startBtn:
        document.getElementById("start-btn"),

    stopBtn:
        document.getElementById("stop-btn"),


    fileSelect:
        document.getElementById("file-select"),

    saveBtn:
        document.getElementById("save-btn"),

};





// -------------------------------
// 状態取得
// -------------------------------


async function fetchStatus() {


    try {


        const response =
            await fetch("/status");


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();



        renderStatus(data);



        el.connectionStatus.textContent =
            "正常";


        el.connectionStatus.className =
            "value state-fix";



    } catch(error) {



        el.connectionStatus.textContent =
            "通信エラー";


        el.connectionStatus.className =
            "value state-error";


    }

}





// -------------------------------
// 状態表示
// -------------------------------


function renderStatus(data) {



    el.currentTime.textContent =
        data.current_time ?? "--";



    if(data.running){


        el.runningState.textContent =
            "計測中";


        el.runningState.className =
            "value state-running";


    }else{


        el.runningState.textContent =
            "停止中";


        el.runningState.className =
            "value state-stopped";

    }




    el.message.textContent =
        data.message ?? "--";





    const sat =
        data.satellites ?? 0;



    if(data.gps_fix){


        el.gpsFix.textContent =
            `測位中 (${sat}衛星)`;


        el.gpsFix.className =
            "value state-fix";



    }else{


        el.gpsFix.textContent =
            `未測位 (${sat}衛星)`;


        el.gpsFix.className =
            "value state-nofix";


    }




    el.latitude.textContent =
        formatCoordinate(
            data.latitude
        );


    el.longitude.textContent =
        formatCoordinate(
            data.longitude
        );





    if(
        data.temperature === null ||
        data.temperature === undefined
    ){

        el.temperature.textContent =
            "-- ℃";


    }else{


        el.temperature.textContent =
            `${Number(data.temperature).toFixed(2)} ℃`;

    }





    el.records.textContent =
        data.records ?? "--";


    el.filename.textContent =
        data.filename || "--";





    el.startBtn.disabled =
        Boolean(data.running);


    el.stopBtn.disabled =
        !data.running;





    updateMap(

        data.latitude,

        data.longitude,

        data.gps_fix

    );


}





function formatCoordinate(value){


    if(
        value === null ||
        value === undefined
    ){

        return "--";

    }


    return Number(value).toFixed(6);

}







// -------------------------------
// 計測開始
// -------------------------------


async function handleStart(){


    el.startBtn.disabled = true;


    try{


        const response =
            await fetch(
                "/start",
                {
                    method:"POST"
                }
            );


        if(!response.ok){

            throw new Error();

        }


        await fetchStatus();



    }catch(error){


        el.connectionStatus.textContent =
            "通信エラー";


    }


}







// -------------------------------
// 計測停止
// -------------------------------


async function handleStop(){


    el.stopBtn.disabled = true;


    try{


        const response =
            await fetch(
                "/stop",
                {
                    method:"POST"
                }
            );


        if(!response.ok){

            throw new Error();

        }


        await fetchStatus();



    }catch(error){


        el.connectionStatus.textContent =
            "通信エラー";


    }

}








// -------------------------------
// ファイル一覧
// -------------------------------


function formatFileLabel(name){


    const match =
        name.match(
            /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.csv$/i
        );


    if(!match){

        return name;

    }



    const [
        ,
        year,
        month,
        day,
        hour,
        minute,
        second

    ] = match;



    return `${year}年${month}月${day}日 ${hour}:${minute}:${second}`;

}





async function fetchFileList(){


    try{


        const response =
            await fetch("/files");


        const data =
            await response.json();


        renderFileList(
            data.files ?? []
        );


    }catch(error){



    }


}






function renderFileList(fileList){


    const previousValue =
        el.fileSelect.value;



    el.fileSelect.innerHTML = "";




    for(const name of fileList){


        const option =
            document.createElement("option");


        option.value =
            name;


        option.textContent =
            formatFileLabel(name);


        el.fileSelect.appendChild(option);


    }




    if(
        fileList.includes(previousValue)
    ){

        el.fileSelect.value =
            previousValue;

    }




    el.saveBtn.disabled =
        fileList.length === 0;


}







function handleSave(){


    const selected =
        el.fileSelect.value;



    if(!selected){

        return;

    }


    window.location.href =
        `/download/${encodeURIComponent(selected)}`;


}









// -------------------------------
// 地図初期化
// -------------------------------

function initMap(){

    map = L.map("map").setView([34.8093, 135.5617], 15);

    L.tileLayer("/tiles/{z}/{x}/{y}.png", {
        maxZoom: 18,
    }).addTo(map);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    trackLine = L.polyline([], {}).addTo(map);
    csvTrackLine = L.polyline([], {}).addTo(map);
}

// -------------------------------
// 現在位置＋軌跡更新
// -------------------------------


function updateMap(

    latitude,

    longitude,

    gpsFix

){



    if(!map){

        return;

    }



    if(!gpsFix){

        return;

    }



    if(

        latitude === 0 ||

        longitude === 0

    ){

        return;

    }




    const position =

    [

        latitude,

        longitude

    ];







    if(!currentMarker){



        currentMarker =

            L.marker(position)

            .addTo(map);




        map.setView(

            position,

            17

        );




    }else{


        currentMarker.setLatLng(

            position

        );



        map.panTo(

            position

        );


    }







    // 軌跡追加


    const last =

        trackPoints[
            trackPoints.length - 1
        ];





    if(

        !last ||

        last[0] !== latitude ||

        last[1] !== longitude

    ){



        trackPoints.push(

            position

        );



        trackLine.setLatLngs(

            trackPoints

        );



    }





}









// -------------------------------
// 起動
// -------------------------------


el.startBtn.addEventListener(
    "click",
    handleStart
);


el.stopBtn.addEventListener(
    "click",
    handleStop
);


el.saveBtn.addEventListener(
    "click",
    handleSave
);

el.fileSelect.addEventListener(
    "change",
    handleCSVSelect
);

initMap();


fetchStatus();


fetchFileList();



setInterval(

    fetchStatus,

    POLL_INTERVAL_MS

);



setInterval(

    fetchFileList,

    POLL_INTERVAL_MS * 5

);
// -------------------------------
// CSV選択時の軌跡表示
// -------------------------------

async function handleCSVSelect(){


    const filename =
        el.fileSelect.value;


    if(!filename){

        return;

    }



    try{


        const response =
            await fetch(
                `/track/${encodeURIComponent(filename)}`
            );


        if(!response.ok){

            throw new Error(
                "track取得失敗"
            );

        }



        const data =
            await response.json();



        const points =
            data.points ?? [];



        csvTrackLine.setLatLngs(
            points
        );



        if(points.length > 0){


            map.fitBounds(
                csvTrackLine.getBounds()
            );


        }



    }catch(error){


        console.log(
            "CSV軌跡表示エラー:",
            error
        );


    }

}
const mapDownloadBtn = document.getElementById("map-download-btn");
const mapCancelBtn = document.getElementById("map-cancel-btn");
const mapNameInput = document.getElementById("map-name-input");
const mapDownloadMessage = document.getElementById("map-download-message");
const mapDownloadProgress = document.getElementById("map-download-progress");
const mapTotalSize = document.getElementById("map-total-size");
const mapRegionList = document.getElementById("map-region-list");

let downloadPolling = null;

function formatBytes(bytes) {
    if (!bytes) return "0 MB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

async function handleMapDownload() {

    const name = mapNameInput.value.trim();

    if (!name) {
        mapDownloadMessage.textContent = "地図名を入力してください";
        return;
    }

    const bounds = map.getBounds();

    const payload = {
        name: name,
        south: bounds.getSouth(),
        west: bounds.getWest(),
        north: bounds.getNorth(),
        east: bounds.getEast(),
    };

    mapDownloadBtn.disabled = true;

    try {
        const response = await fetch("/maps/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!data.success) {
            mapDownloadMessage.textContent = data.message || "開始できませんでした";
            mapDownloadBtn.disabled = false;
            return;
        }

        mapDownloadMessage.textContent = `ダウンロード中(全${data.total}枚)`;
        mapCancelBtn.disabled = false;

        startDownloadPolling();

    } catch (error) {
        mapDownloadMessage.textContent = "通信エラー";
        mapDownloadBtn.disabled = false;
    }
}

async function handleMapCancel() {

    mapCancelBtn.disabled = true;

    try {
        await fetch("/maps/download/cancel", { method: "POST" });
    } catch (error) {
        // 無視
    }
}

function startDownloadPolling() {

    if (downloadPolling) return;

    downloadPolling = setInterval(async () => {

        const response = await fetch("/maps/download/status");
        const data = await response.json();

        mapDownloadMessage.textContent = data.message;
        mapDownloadProgress.textContent = `${data.done} / ${data.total}(スキップ${data.skipped} 失敗${data.failed})`;

        if (!data.running) {
            clearInterval(downloadPolling);
            downloadPolling = null;
            mapDownloadBtn.disabled = false;
            mapCancelBtn.disabled = true;
            mapNameInput.value = "";
            fetchMapRegions();
        }

    }, 1000);
}

async function fetchMapRegions() {

    try {

        const response = await fetch("/maps/regions");
        const data = await response.json();

        mapTotalSize.textContent =
            `${formatBytes(data.total_bytes)} / ${formatBytes(data.limit_bytes)}`;

        mapRegionList.innerHTML = "";

        for (const region of data.regions) {

            const row = document.createElement("div");
            row.className = "row";

            const label = document.createElement("span");
            label.className = "label";
            label.textContent =
                `${region.name}(${formatBytes(region.size_bytes)})`;

            const delBtn = document.createElement("button");
            delBtn.className = "btn stop";
            delBtn.textContent = "削除";
            delBtn.style.padding = "4px 12px";
            delBtn.style.fontSize = "13px";
            delBtn.addEventListener("click", () => handleRegionDelete(region.id));

            row.appendChild(label);
            row.appendChild(delBtn);
            mapRegionList.appendChild(row);
        }

    } catch (error) {
        // 無視
    }
}

async function handleRegionDelete(regionId) {

    try {
        await fetch(`/maps/regions/${regionId}`, { method: "DELETE" });
        fetchMapRegions();
    } catch (error) {
        // 無視
    }
}

mapDownloadBtn.addEventListener("click", handleMapDownload);
mapCancelBtn.addEventListener("click", handleMapCancel);

fetchMapRegions();
setInterval(fetchMapRegions, 10000);

const mapDownloadCard =
    document.getElementById("map-download-card");


async function checkWiredStatus(){


    try{

        const response =
            await fetch("/network/status");

        const data =
            await response.json();


        mapDownloadCard.style.display =
            data.wired ? "block" : "none";


    }catch(error){

        mapDownloadCard.style.display = "none";

    }


}


checkWiredStatus();


setInterval(
    checkWiredStatus,
    5000
);

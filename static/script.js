* {
    box-sizing: border-box;
}
body {
    margin: 0;
    padding: 16px;
    background-color: #f2f4f7;
    font-family: "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif;
    color: #222;
}
.container {
    max-width: 480px;
    margin: 0 auto;
}
h1 {
    text-align: center;
    font-size: 22px;
    margin: 8px 0 20px 0;
    color: #1a237e;
}
h2 {
    font-size: 16px;
    margin: 0 0 10px 0;
    color: #555;
}
.card {
    background: #ffffff;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}
.row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid #eee;
}
.row:last-child {
    border-bottom: none;
}
.label {
    font-size: 14px;
    color: #777;
}
.value {
    font-size: 16px;
    font-weight: bold;
    color: #222;
}
/* 水温表示 */
.temperature-value {
    font-size: 30px;
}
.button-card {
    display: flex;
    gap: 12px;
}
.btn {
    flex: 1;
    padding: 16px 0;
    font-size: 17px;
    font-weight: bold;
    border: none;
    border-radius: 10px;
    color: #fff;
    cursor: pointer;
    transition: opacity 0.15s ease-in-out;
}
.btn:active {
    opacity: 0.75;
}
.btn.start {
    background-color: #4caf50;
}
.btn.stop {
    background-color: #f44336;
}
.btn.save {
    background-color: #2196f3;
    width: 100%;
    margin-top: 10px;
}
.file-select {
    width: 100%;
    padding: 12px;
    font-size: 15px;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #fafafa;
    color: #222;
}
.btn:disabled {
    background-color: #bdbdbd;
    cursor: not-allowed;
}
/* 状態による色分け */
.state-running {
    color: #2e7d32;
}
.state-stopped {
    color: #c62828;
}
.state-fix {
    color: #2e7d32;
}
.state-nofix {
    color: #c62828;
}
.state-error {
    color: #c62828;
}
@media (min-width: 600px) {
    body {
        padding: 32px;
    }
    h1 {
        font-size: 26px;
    }
    .temperature-value {
        font-size: 34px;
    }
}
/* ================================
   地図表示
   ================================ */
#map {
    width: 100%;
    height: 300px;
    border-radius: 10px;
}
#map-out-of-coverage {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    background-image: repeating-linear-gradient(
        45deg,
        rgba(255, 214, 0, 0.55),
        rgba(255, 214, 0, 0.55) 12px,
        rgba(40, 40, 40, 0.55) 12px,
        rgba(40, 40, 40, 0.55) 24px
    );
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    z-index: 500;
}
#map-out-of-coverage span {
    background: rgba(0, 0, 0, 0.7);
    color: #fff;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}

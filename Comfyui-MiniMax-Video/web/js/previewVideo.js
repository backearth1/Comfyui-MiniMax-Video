// Based on https://github.com/ArtVentureX/comfyui-animatediff/blob/main/web/js/vid_preview.js
import { app } from '../../../scripts/app.js';
import { createImageHost } from "../../../scripts/ui/imagePreview.js"

const BASE_SIZE = 768;
const PREVIEW_WIDTH = 320;  // 单个预览宽度
const PREVIEW_HEIGHT = 240; // 单个预览高度
const PREVIEW_GAP = 10;    // 预览间距
const GRID_PADDING = 15;   // 网格内边距

function setVideoDimensions(videoElement, width, height) {
    videoElement.style.width = `${width}px`;
    videoElement.style.height = `${height}px`;
}

export function resizeVideoAspectRatio(videoElement, maxWidth, maxHeight) {
    const aspectRatio = videoElement.videoWidth / videoElement.videoHeight;
    let newWidth, newHeight;

    if (videoElement.videoWidth / maxWidth > videoElement.videoHeight / maxHeight) {
        newWidth = maxWidth;
        newHeight = newWidth / aspectRatio;
    } else {
        newHeight = maxHeight;
        newWidth = newHeight * aspectRatio;
    }

    setVideoDimensions(videoElement, newWidth, newHeight);
    return { width: newWidth, height: newHeight + 10 };
}

export function chainCallback(object, property, callback) {
    if (object == undefined) {
        console.error("Tried to add callback to non-existant object");
        return;
    }
    if (property in object) {
        const callback_orig = object[property];
        object[property] = function () {
            const r = callback_orig.apply(this, arguments);
            callback.apply(this, arguments);
            return r;
        };
    } else {
        object[property] = callback;
    }
}

// 计算网格布局
function calculateGrid(count) {
    if (count <= 1) return { rows: 1, cols: 1 };
    if (count <= 4) return { rows: 2, cols: 2 };
    return { rows: 2, cols: 3 };  // 5-6个视频
}

export function addVideoPreview(nodeType, options = {}) {
    const videoMap = new Map();

    const createVideoNode = (url, index) => {
        return new Promise((resolve) => {
            if (videoMap.has(url)) {
                const existingVideo = videoMap.get(url);
                if (existingVideo.video && !existingVideo.video.error) {
                    resolve(existingVideo);
                    return;
                }
            }

            const container = document.createElement('div');
            container.className = 'video-preview-container';
            container.style.position = 'relative';
            container.style.width = `${PREVIEW_WIDTH}px`;
            container.style.height = `${PREVIEW_HEIGHT + 30}px`;
            container.style.backgroundColor = '#1a1a1a';
            container.style.borderRadius = '8px';
            container.style.overflow = 'hidden';
            
            const title = document.createElement('div');
            title.textContent = `Task #${index + 1}`;
            title.style.padding = '5px 10px';
            title.style.color = '#fff';
            title.style.fontSize = '14px';
            title.style.fontWeight = 'bold';
            title.style.textAlign = 'center';
            container.appendChild(title);

            const videoContainer = document.createElement('div');
            videoContainer.style.width = `${PREVIEW_WIDTH}px`;
            videoContainer.style.height = `${PREVIEW_HEIGHT}px`;
            videoContainer.style.display = 'flex';
            videoContainer.style.alignItems = 'center';
            videoContainer.style.justifyContent = 'center';
            videoContainer.style.overflow = 'hidden';
            container.appendChild(videoContainer);

            const videoEl = document.createElement('video');
            videoEl.style.maxWidth = '100%';
            videoEl.style.maxHeight = '100%';
            videoEl.style.objectFit = 'contain';
            
            videoEl.muted = true;
            videoEl.loop = true;
            videoEl.playsInline = true;
            videoEl.controls = false;
            videoEl.preload = 'metadata';
            
            let loadStarted = false;
            let playAttempts = 0;
            const MAX_PLAY_ATTEMPTS = 3;

            const tryPlay = async () => {
                if (playAttempts >= MAX_PLAY_ATTEMPTS) return;
                try {
                    await videoEl.play();
                    playAttempts = 0;
                } catch (e) {
                    console.warn(`视频 #${index + 1} 播放尝试 ${playAttempts + 1} 失败:`, e);
                    playAttempts++;
                    setTimeout(tryPlay, 1000);
                }
            };

            videoEl.addEventListener('loadedmetadata', () => {
                if (!loadStarted) {
                    loadStarted = true;
                    videoContainer.appendChild(videoEl);
                    tryPlay();
                    const result = { element: container, video: videoEl };
                    videoMap.set(url, result);
                    resolve(result);
                }
            });

            videoEl.addEventListener('error', () => {
                console.error(`视频 #${index + 1} 加载失败:`, videoEl.error);
                videoMap.delete(url);
                resolve(null);
            });

            videoEl.src = url;
        });
    };

    nodeType.prototype.onDrawBackground = function (ctx) {
        if (this.flags.collapsed) return;

        const imageURLs = this.images ?? [];
        const currentUrls = JSON.stringify(imageURLs);
        
        if (!this.previewContainer || 
            !this.displayingImages || 
            JSON.stringify(this.displayingImages) !== currentUrls) {
            
            this.displayingImages = JSON.parse(currentUrls);
            
            // 创建网格容器
            const gridContainer = document.createElement('div');
            gridContainer.style.display = 'flex';
            gridContainer.style.flexDirection = 'column';
            gridContainer.style.gap = `${PREVIEW_GAP}px`;
            gridContainer.style.padding = `${GRID_PADDING}px`;
            gridContainer.style.backgroundColor = '#2a2a2a';
            gridContainer.style.borderRadius = '10px';

            Promise.all(imageURLs.map((url, index) => createVideoNode(url, index)))
                .then(results => {
                    results = results.filter(r => r);
                    if (results.length === 0) return;

                    // 计算网格布局
                    const grid = calculateGrid(results.length);
                    
                    // 创建行容器
                    const rows = [];
                    for (let i = 0; i < grid.rows; i++) {
                        const row = document.createElement('div');
                        row.style.display = 'flex';
                        row.style.gap = `${PREVIEW_GAP}px`;
                        row.style.justifyContent = 'center';
                        rows.push(row);
                        gridContainer.appendChild(row);
                    }

                    // 分配视频到网格
                    results.forEach((result, index) => {
                        if (result?.element) {
                            const rowIndex = Math.floor(index / grid.cols);
                            if (rowIndex < rows.length) {
                                rows[rowIndex].appendChild(result.element);
                            }
                        }
                    });

                    // 计算节点大小
                    const totalWidth = (grid.cols * PREVIEW_WIDTH) + 
                                    ((grid.cols - 1) * PREVIEW_GAP) + 
                                    (GRID_PADDING * 2);
                    const totalHeight = (grid.rows * (PREVIEW_HEIGHT + 30)) + 
                                     ((grid.rows - 1) * PREVIEW_GAP) + 
                                     (GRID_PADDING * 2);

                    this.size[0] = totalWidth;
                    this.size[1] = totalHeight;

                    // 更新预览widget
                    const widgetIdx = this.widgets?.findIndex(w => w.name === "preview");
                    if (widgetIdx > -1) {
                        const widget = this.widgets[widgetIdx];
                        if (widget.options.host.el.firstChild) {
                            widget.options.host.el.replaceChild(
                                gridContainer, 
                                widget.options.host.el.firstChild
                            );
                        } else {
                            widget.options.host.el.appendChild(gridContainer);
                        }
                    } else {
                        const host = createImageHost(this);
                        host.el.appendChild(gridContainer);
                        this.addDOMWidget("preview", "img", host.el, {
                            host,
                            getValue() { return host.value; },
                            setValue(v) { /* nothing */ }
                        });
                    }

                    this.imgs = results.map(r => r.video);
                    this.previewContainer = gridContainer;

                    requestAnimationFrame(() => {
                        this.setDirtyCanvas(true, true);
                    });
                })
                .catch(error => {
                    console.error("创建视频预览时发生错误:", error);
                });
        }
    };

    chainCallback(nodeType.prototype, "onExecuted", function (message) {
        if (message?.video_url) {
            const urls = Array.isArray(message.video_url) ? 
                message.video_url : [message.video_url];
            
            if (JSON.stringify(this.images) !== JSON.stringify(urls)) {
                this.images = urls;
                this.setDirtyCanvas(true);
            }
        }
    });
}

app.registerExtension({
    name: "MiniMaxVideoPreview",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "MiniMaxPreviewVideo") {
            return;
        }
        addVideoPreview(nodeType);
    },
});
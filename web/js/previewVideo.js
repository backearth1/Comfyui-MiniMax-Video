// Based on https://github.com/ArtVentureX/comfyui-animatediff/blob/main/web/js/vid_preview.js
import { app } from '../../../scripts/app.js';
import { createImageHost } from "../../../scripts/ui/imagePreview.js"

const BASE_SIZE = 768;

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

export function addVideoPreview(nodeType, options = {}) {
    const createVideoNode = (url) => {
        return new Promise((cb) => {
            const videoEl = document.createElement('video');
            videoEl.addEventListener('loadedmetadata', () => {
                videoEl.controls = false;
                videoEl.loop = true;
                videoEl.muted = true;
                const dimensions = resizeVideoAspectRatio(videoEl, BASE_SIZE, BASE_SIZE);
                cb({ element: videoEl, dimensions: dimensions });
            });
            videoEl.addEventListener('error', () => {
                cb();
            });
            videoEl.src = url;
        });
    };

    const origInputs = nodeType.prototype.getExtraMenuOptions;
    nodeType.prototype.getExtraMenuOptions = function(_, options) {
        const result = origInputs ? origInputs.apply(this, arguments) : [];
        result.push({
            content: "设置预览高度",
            callback: () => {
                const height = parseInt(prompt("输入预览高度 (像素)", this.previewHeight || BASE_SIZE));
                if (!isNaN(height)) {
                    this.previewHeight = height;
                    if (this.imgs?.[0]) {
                        const dimensions = resizeVideoAspectRatio(this.imgs[0], BASE_SIZE, height);
                        this.size[0] = dimensions.width;
                        this.size[1] = dimensions.height;
                        this.setDirtyCanvas(true, true);
                    }
                }
            }
        });
        return result;
    };

    nodeType.prototype.onDrawBackground = function (ctx) {
        if (this.flags.collapsed) return;

        let imageURLs = this.images ?? [];
        let imagesChanged = false;

        if (JSON.stringify(this.displayingImages) !== JSON.stringify(imageURLs)) {
            this.displayingImages = imageURLs;
            imagesChanged = true;
        }

        if (!imagesChanged) {
            return;
        }

        if (!imageURLs.length) {
            this.imgs = null;
            this.animatedImages = false;
            return;
        }

        const promises = imageURLs.map((url) => {
            return createVideoNode(url);
        });

        Promise.all(promises)
            .then((results) => {
                this.imgs = results.filter(r => r).map(r => r.element);
                if (results[0]) {
                    const dimensions = resizeVideoAspectRatio(
                        this.imgs[0], 
                        BASE_SIZE, 
                        this.previewHeight || BASE_SIZE
                    );
                    this.size[0] = dimensions.width;
                    this.size[1] = dimensions.height;
                }
            })
            .then(() => {
                if (!this.imgs?.length) return;

                this.animatedImages = true;
                const widgetIdx = this.widgets?.findIndex((w) => w.name === "preview");

                if (widgetIdx > -1) {
                    const widget = this.widgets[widgetIdx];
                    widget.options.host.updateImages(this.imgs);
                } else {
                    const host = createImageHost(this);
                    const widget = this.addDOMWidget("preview", "img", host.el, {
                        host,
                        getValue() { return host.value; },
                        setValue(v) { /* nothing */ }
                    });
                    widget.options.host.updateImages(this.imgs);
                }

                this.imgs.forEach((img) => {
                    if (img instanceof HTMLVideoElement) {
                        img.muted = true;
                        img.autoplay = true;
                        img.play();
                    }
                });

                this.setDirtyCanvas(true, true);
            });
    };

    chainCallback(nodeType.prototype, "onExecuted", function (message) {
        if (message?.video_url) {
            this.images = message?.video_url;
            this.setDirtyCanvas(true);
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
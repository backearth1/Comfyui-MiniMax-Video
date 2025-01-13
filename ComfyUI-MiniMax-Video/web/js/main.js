import { app } from '../../../scripts/app.js';
import { addVideoPreview } from './previewVideo.js';

app.registerExtension({
    name: "MiniMax.VideoPreview",
    async setup() {
        console.log("%c MiniMax 扩展设置", "color: #9C27B0;");
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "MiniMaxPreviewVideo") {
            console.log("%c 注册视频预览节点", "color: #FF9800;");
            
            // 调整节点的最小尺寸
            nodeType.size = nodeType.size || [350, 350];
            nodeType.min_height = 100; // 设置最小高度
            nodeType.min_width = 350;  // 设置最小宽度
            
            // 添加预览功能
            addVideoPreview(nodeType);
        }
    }
});

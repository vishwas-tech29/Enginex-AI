# Component design

## Frontend component map

### App shell
- AppShell: top navigation, project switcher, left rail, right rail, command palette
- ProjectNavigator: folder tree and recent projects
- WorkspaceSurface: hosts CAD, PCB, or AI views in tabs

### CAD editor components
- CADCanvas: renders a 2D/3D canvas and handles interaction state
- Toolbar: tool selection, object creation, transform operations
- PropertyPanel: feature properties, constraints, parameter values
- LayerPanel: object tree, visibility, lock state
- Viewport: camera controls, grid, snapping, measurement tools

### PCB editor components
- SchematicCanvas: schematic editing surface
- LayoutCanvas: placement and routing surface
- DesignRulePanel: DRC, net classes, clearance checks

### AI assistant components
- ChatPanel: renders assistant messages and tool outputs
- AgentSwitcher: selects planner, CAD, PCB, electronics, or documentation workflows
- MessageComposer: file attachments, multimodal input, prompt presets

## Props and responsibilities

```ts
interface CADCanvasProps {
  documentId: string;
  viewport: ViewportState;
  onSelect: (ids: string[]) => void;
  onCommitChange: (change: ChangeEvent) => Promise<void>;
}
```

```ts
interface ChatPanelProps {
  chatId: string;
  messages: Message[];
  onSendMessage: (content: string) => Promise<void>;
  isStreaming: boolean;
}
```

## Hooks

- useCADEditor: maintains editing commands, selection, and viewport state
- usePCBEditor: manages board state, placement, and DRC status
- useAIAssistant: owns streaming messages, agent selection, and tool execution
- useUndo: maintains command history for collaborative editing
- useSnapping: computes snap targets and constraint guidance

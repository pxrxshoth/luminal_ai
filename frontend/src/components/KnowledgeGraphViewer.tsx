import React, { useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useAppStore } from '../store/useAppStore';
import { Network } from 'lucide-react';

export const KnowledgeGraphViewer: React.FC = () => {
  const { graphData, activeTopic } = useAppStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = React.useState({ width: 800, height: 600 });

  useEffect(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      setDimensions({ width: clientWidth, height: clientHeight });
    }
    
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const dummyData = {
    nodes: [
      { id: '1', name: 'Artificial Intelligence', val: 10 },
      { id: '2', name: 'Machine Learning', val: 8 },
      { id: '3', name: 'Deep Learning', val: 6 },
      { id: '4', name: 'Neural Networks', val: 6 },
      { id: '5', name: 'Transformer', val: 4 }
    ],
    links: [
      { source: '1', target: '2', name: 'INCLUDES' },
      { source: '2', target: '3', name: 'INCLUDES' },
      { source: '3', target: '4', name: 'USES' },
      { source: '4', target: '5', name: 'ARCHITECTURE' }
    ]
  };

  const dataToRender = graphData.nodes.length > 0 ? graphData : dummyData;

  return (
    <div className="flex-1 flex flex-col h-full bg-gray-950 relative">
      <div className="absolute top-4 left-4 z-10 bg-gray-900/80 backdrop-blur-md border border-gray-800 p-4 rounded-xl shadow-2xl">
        <h3 className="text-gray-100 font-semibold flex items-center gap-2">
          <Network className="text-emerald-500" size={18} />
          Conceptual Topology
        </h3>
        <p className="text-gray-400 text-xs mt-1">
          {activeTopic ? `Traversing: ${activeTopic}` : 'Awaiting semantic intent...'}
        </p>
      </div>
      
      <div className="flex-1 w-full h-full" ref={containerRef}>
        <ForceGraph2D
          width={dimensions.width}
          height={dimensions.height}
          graphData={dataToRender}
          nodeLabel="name"
          nodeColor={() => '#3b82f6'}
          linkColor={() => '#4b5563'}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.2}
          backgroundColor="#030712"
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12/globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            ctx.fillStyle = 'rgba(3, 7, 18, 0.8)';
            ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = node.color;
            ctx.fillText(label, node.x, node.y);

            node.__bckgDimensions = bckgDimensions;
          }}
          nodePointerAreaPaint={(node: any, color, ctx) => {
            ctx.fillStyle = color;
            const bckgDimensions = node.__bckgDimensions;
            bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);
          }}
        />
      </div>
    </div>
  );
};

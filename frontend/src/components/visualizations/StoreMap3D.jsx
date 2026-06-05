import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Html } from '@react-three/drei';
import GlassCard from '../ui/GlassCard';

function Shelf({ position, color = "#4f46e5", label, stock }) {
    const mesh = useRef();
    const [hovered, setHover] = useState(false);

    useFrame((state, delta) => {
        if (hovered) {
            mesh.current.rotation.y += delta;
        } else {
            mesh.current.rotation.y = 0;
        }
    });

    return (
        <group position={position}>
            <mesh
                ref={mesh}
                onPointerOver={() => setHover(true)}
                onPointerOut={() => setHover(false)}
            >
                <boxGeometry args={[1.5, 2, 0.5]} />
                <meshStandardMaterial color={hovered ? "#ec4899" : color} opacity={0.8} transparent />
            </mesh>
            <Text
                position={[0, 1.5, 0]}
                fontSize={0.3}
                color="white"
                anchorX="center"
                anchorY="middle"
            >
                {label}
            </Text>
            {hovered && (
                <Html position={[0, 2.5, 0]}>
                    <div className="bg-black/80 text-white p-2 rounded text-xs whitespace-nowrap border border-white/20 backdrop-blur-md">
                        Stock Level: {stock}%
                    </div>
                </Html>
            )}
        </group>
    );
}

function Floor() {
    return (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
            <planeGeometry args={[20, 20]} />
            <meshStandardMaterial color="#1f2937" />
            <gridHelper args={[20, 20, 0xffffff, 0x555555]} rotation={[-Math.PI / 2, 0, 0]} />
        </mesh>
    );
}

const StoreMap3D = () => {
    return (
        <div className="h-[500px] w-full bg-gray-900 rounded-xl overflow-hidden relative">
            <Canvas camera={{ position: [5, 5, 8], fov: 50 }}>
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} />

                <Floor />

                {/* Shelves Layout */}
                <Shelf position={[-3, 0, -2]} label="Electronics" stock={85} />
                <Shelf position={[0, 0, -2]} label="Apparel" stock={40} color="#facc15" />
                <Shelf position={[3, 0, -2]} label="Home" stock={90} />

                <Shelf position={[-3, 0, 2]} label="Sports" stock={15} color="#ef4444" />
                <Shelf position={[0, 0, 2]} label="Beauty" stock={60} />
                <Shelf position={[3, 0, 2]} label="Toys" stock={75} />

                <OrbitControls minPolarAngle={0} maxPolarAngle={Math.PI / 2.1} />
            </Canvas>

            <div className="absolute top-4 left-4 pointer-events-none">
                <GlassCard className="p-3">
                    <h3 className="text-white font-bold text-sm">Live Store Digital Twin</h3>
                    <p className="text-gray-400 text-xs">Based on IoT Senor Data</p>
                </GlassCard>
            </div>
        </div>
    );
};

export default StoreMap3D;

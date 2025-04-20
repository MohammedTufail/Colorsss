import React, { useRef, useState, useEffect } from "react";
import axios from "axios";

type ColorInfo = {
  color: string;
  proportion: number;
};

export default function PaletteExtractor() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [image, setImage] = useState<string | null>(null);
  const [fileBlob, setFileBlob] = useState<Blob | null>(null);
  const [selection, setSelection] = useState<{
    x: number;
    y: number;
    width: number;
    height: number;
  } | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [colors, setColors] = useState<ColorInfo[]>([]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileBlob(file);
    const url = URL.createObjectURL(file);
    setImage(url);
    setSelection(null);
    setColors([]);
  };

  const startDraw = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    setSelection({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      width: 0,
      height: 0,
    });
    setDrawing(true);
  };

  const drawRect = (e: React.MouseEvent) => {
    if (!drawing || !selection) return;
    const rect = canvasRef.current!.getBoundingClientRect();
    const width = e.clientX - rect.left - selection.x;
    const height = e.clientY - rect.top - selection.y;
    setSelection({ ...selection, width, height });
  };

  const endDraw = () => {
    setDrawing(false);
    if (selection && fileBlob) {
      const formData = new FormData();
      formData.append("image", fileBlob);
      formData.append("x", selection.x.toString());
      formData.append("y", selection.y.toString());
      formData.append("width", selection.width.toString());
      formData.append("height", selection.height.toString());

      axios
        .post<ColorInfo[]>("http://localhost:5003/extract_palette", formData)
        .then((res) => {
          setColors(res.data);
        });
    }
  };

  useEffect(() => {
    if (!image || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.src = image;

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx?.drawImage(img, 0, 0);
      if (selection && ctx) {
        ctx.strokeStyle = "blue";
        ctx.lineWidth = 2;
        ctx.strokeRect(
          selection.x,
          selection.y,
          selection.width,
          selection.height
        );
      }
    };
  }, [image, selection]);

  return (
    <div className="p-4 space-y-4 max-w-[640px]">
      <input type="file" accept="image/*" onChange={handleImageUpload} />

      {image && (
        <div className="relative border inline-block">
          <canvas
            ref={canvasRef}
            onMouseDown={startDraw}
            onMouseMove={drawRect}
            onMouseUp={endDraw}
            className="cursor-crosshair"
            style={{ maxWidth: "100%", height: "auto" }}
          />
        </div>
      )}

      {colors.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xl font-bold mb-2">Extracted Palette</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {colors.map((color, index) => (
              <div
                key={index}
                className="rounded overflow-hidden border shadow-sm"
                style={{ backgroundColor: color.color }}
              >
                <div className="p-2 bg-white/70 backdrop-blur text-sm font-medium text-black">
                  <span>{color.color}</span>
                  <br />
                  <span>{(color.proportion * 100).toFixed(2)}%</span>
                </div>
                <div className="h-20" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

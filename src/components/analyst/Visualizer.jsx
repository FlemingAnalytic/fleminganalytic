import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { PieChart as PieIcon, BarChart2 } from 'lucide-react';

const Visualizer = ({ dataset }) => {
  if (!dataset || !dataset.preview) return null;

  const chartData = dataset.preview.slice(0, 20);
  const keys = Object.keys(chartData[0]);
  const numericKey = keys.find(k => typeof chartData[0][k] === 'number') || keys[1];

  return (
    <div className="space-y-12">
      <div className="bg-[#0A0A0A] border border-white/[0.05] p-12 rounded-[32px] shadow-2xl">
        <div className="flex justify-between items-center mb-10">
          <h3 className="text-sm font-black uppercase tracking-widest opacity-40 flex items-center gap-4">
            <BarChart2 size={16} /> Data Distribution: {numericKey}
          </h3>
        </div>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
              <XAxis dataKey={keys[0]} stroke="#ffffff30" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="#ffffff30" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#000', border: '1px solid #ffffff10', borderRadius: '12px', fontSize: '10px' }}
                itemStyle={{ color: '#3b82f6' }}
              />
              <Area type="monotone" dataKey={numericKey} stroke="#3b82f6" fillOpacity={1} fill="url(#colorValue)" strokeWidth={3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="p-10 border border-white/5 bg-white/[0.02] rounded-3xl flex flex-col items-center justify-center text-center space-y-4">
           <PieIcon size={40} className="text-purple-500/20" />
           <p className="text-[10px] font-black uppercase tracking-widest text-white/30">Categorical Breakdown Logic Initializing...</p>
        </div>
        <div className="p-10 border border-white/5 bg-white/[0.02] rounded-3xl flex flex-col items-center justify-center text-center space-y-4">
           <BarChart2 size={40} className="text-blue-500/20" />
           <p className="text-[10px] font-black uppercase tracking-widest text-white/30">Cross-Feature Comparison Matrix...</p>
        </div>
      </div>
    </div>
  );
};

export default Visualizer;

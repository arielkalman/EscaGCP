import React from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { AnalysisResults } from '../../types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  TrendingUp, 
  PieChart as PieChartIcon, 
  BarChart3,
  Activity 
} from 'lucide-react';

interface DashboardChartsProps {
  analysisData: AnalysisResults;
}

export function DashboardCharts({ analysisData }: DashboardChartsProps) {
  // Mock data for attack path distribution
  const attackPathData = [
    { name: 'Critical', value: analysisData.attack_paths.critical?.length || 0, color: '#DC2626' },
    { name: 'High', value: analysisData.attack_paths.high?.length || 0, color: '#EA580C' },
    { name: 'Medium', value: analysisData.attack_paths.medium?.length || 0, color: '#D97706' },
    { name: 'Low', value: analysisData.attack_paths.low?.length || 0, color: '#16A34A' },
  ];

  // Mock data for risk score distribution
  const riskScoreData = [
    { range: '0-20%', count: 45, color: '#10B981' },
    { range: '21-40%', count: 32, color: '#F59E0B' },
    { range: '41-60%', count: 18, color: '#EF4444' },
    { range: '61-80%', count: 12, color: '#DC2626' },
    { range: '81-100%', count: 8, color: '#7C2D12' },
  ];

  // Mock data for node type breakdown
  const nodeTypeData = [
    { name: 'Users', value: 25, color: '#3B82F6' },
    { name: 'Service Accounts', value: 35, color: '#10B981' },
    { name: 'Groups', value: 15, color: '#F59E0B' },
    { name: 'Projects', value: 8, color: '#EF4444' },
    { name: 'Resources', value: 17, color: '#8B5CF6' },
  ];

  // Mock trend data for security metrics over time
  const trendData = [
    { month: 'Jan', attackPaths: 23, riskScore: 65 },
    { month: 'Feb', attackPaths: 28, riskScore: 70 },
    { month: 'Mar', attackPaths: 19, riskScore: 58 },
    { month: 'Apr', attackPaths: 15, riskScore: 52 },
    { month: 'May', attackPaths: 12, riskScore: 48 },
    { month: 'Jun', attackPaths: 8, riskScore: 42 },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border border-border rounded-lg shadow-lg p-3">
          <p className="font-medium">{`${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.dataKey}: ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Attack Path Distribution */}
      <Card className="col-span-1">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-red-100 rounded-lg">
              <BarChart3 className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <CardTitle className="text-lg">Attack Path Distribution</CardTitle>
              <CardDescription>
                Breakdown of attack paths by risk level
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={attackPathData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="value" 
                fill="#8884d8"
                radius={[4, 4, 0, 0]}
              >
                {attackPathData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex justify-center mt-4 space-x-4">
            {attackPathData.map((item, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-muted-foreground">
                  {item.name}: {item.value}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Node Type Breakdown */}
      <Card className="col-span-1">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <PieChartIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-lg">Node Type Distribution</CardTitle>
              <CardDescription>
                Composition of entities in your environment
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={nodeTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {nodeTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {nodeTypeData.map((item, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-muted-foreground">
                  {item.name}: {item.value}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Risk Score Histogram */}
      <Card className="col-span-1">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-orange-100 rounded-lg">
              <BarChart3 className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <CardTitle className="text-lg">Risk Score Distribution</CardTitle>
              <CardDescription>
                Histogram of risk scores across all nodes
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskScoreData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="range" 
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="count" 
                fill="#8884d8"
                radius={[4, 4, 0, 0]}
              >
                {riskScoreData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Lower Risk</span>
              <span>Higher Risk</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security Trends */}
      <Card className="col-span-1">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <CardTitle className="text-lg">Security Trends</CardTitle>
              <CardDescription>
                Attack paths and risk score trends over time
              </CardDescription>
            </div>
          </div>
          <div className="flex space-x-2">
            <Badge variant="success">Improving</Badge>
            <Badge variant="default">6 Months</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trendData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="month" 
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                type="monotone"
                dataKey="attackPaths"
                stackId="1"
                stroke="#EF4444"
                fill="#EF4444"
                fillOpacity={0.6}
                strokeWidth={2}
                name="Attack Paths"
              />
              <Area
                type="monotone"
                dataKey="riskScore"
                stackId="2"
                stroke="#F59E0B"
                fill="#F59E0B"
                fillOpacity={0.6}
                strokeWidth={2}
                name="Avg Risk Score"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-4 text-center">
            <div className="space-y-1">
              <p className="text-2xl font-bold text-green-600">-65%</p>
              <p className="text-xs text-muted-foreground">Attack paths reduced</p>
            </div>
            <div className="space-y-1">
              <p className="text-2xl font-bold text-green-600">-35%</p>
              <p className="text-xs text-muted-foreground">Risk score improved</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 
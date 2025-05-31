import { Download, FileText, Database, Image, Archive } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Switch } from '../ui/switch';
import { Separator } from '../ui/separator';
import { useSettings, type ExportFormat } from '../../context/SettingsContext';

export function ExportSettings() {
  const {
    state,
    setExportFormat,
    toggleMetadata,
    toggleCompression,
    toggleAutoRefresh,
    setRefreshInterval
  } = useSettings();

  const handleFormatChange = (value: string) => {
    setExportFormat(value as ExportFormat);
  };

  const getFormatIcon = (format: ExportFormat) => {
    switch (format) {
      case 'json':
        return <Database className="h-4 w-4 text-blue-500" />;
      case 'csv':
        return <FileText className="h-4 w-4 text-green-500" />;
      case 'png':
        return <Image className="h-4 w-4 text-purple-500" />;
      case 'svg':
        return <Image className="h-4 w-4 text-orange-500" />;
      default:
        return <Download className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Export Format */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Download className="h-5 w-5" />
            <span>Export Format</span>
          </CardTitle>
          <CardDescription>
            Choose the default format for exporting data and reports
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label className="text-sm font-medium">Default Format</Label>
            <RadioGroup
              value={state.defaultExportFormat}
              onValueChange={handleFormatChange}
              className="grid grid-cols-1 sm:grid-cols-2 gap-3"
            >
              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="json" id="json" />
                <div className="flex items-center space-x-3 flex-1">
                  {getFormatIcon('json')}
                  <div>
                    <Label htmlFor="json" className="font-medium cursor-pointer">
                      JSON
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Structured data format
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="csv" id="csv" />
                <div className="flex items-center space-x-3 flex-1">
                  {getFormatIcon('csv')}
                  <div>
                    <Label htmlFor="csv" className="font-medium cursor-pointer">
                      CSV
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Spreadsheet compatible
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors opacity-60">
                <RadioGroupItem value="png" id="png" disabled />
                <div className="flex items-center space-x-3 flex-1">
                  {getFormatIcon('png')}
                  <div>
                    <Label htmlFor="png" className="font-medium cursor-pointer">
                      PNG Image
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Coming soon
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors opacity-60">
                <RadioGroupItem value="svg" id="svg" disabled />
                <div className="flex items-center space-x-3 flex-1">
                  {getFormatIcon('svg')}
                  <div>
                    <Label htmlFor="svg" className="font-medium cursor-pointer">
                      SVG Vector
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Coming soon
                    </p>
                  </div>
                </div>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle>Export Options</CardTitle>
          <CardDescription>
            Configure what data is included in exports
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="include-metadata" className="font-medium">
                Include Metadata
              </Label>
              <p className="text-sm text-muted-foreground">
                Add collection timestamps, project info, and analysis details
              </p>
            </div>
            <Switch 
              id="include-metadata"
              checked={state.includeMetadata}
              onCheckedChange={toggleMetadata}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="compress-exports" className="font-medium flex items-center space-x-2">
                <Archive className="h-4 w-4" />
                <span>Compress Exports</span>
              </Label>
              <p className="text-sm text-muted-foreground">
                Create compressed ZIP files for large datasets
              </p>
            </div>
            <Switch 
              id="compress-exports"
              checked={state.compressExports}
              onCheckedChange={toggleCompression}
            />
          </div>
        </CardContent>
      </Card>

      {/* Auto Refresh Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Data Refresh</CardTitle>
          <CardDescription>
            Configure automatic data collection and updates
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="auto-refresh" className="font-medium">
                Auto Refresh
              </Label>
              <p className="text-sm text-muted-foreground">
                Automatically update data at regular intervals
              </p>
            </div>
            <Switch 
              id="auto-refresh"
              checked={state.autoRefresh}
              onCheckedChange={toggleAutoRefresh}
            />
          </div>

          {state.autoRefresh && (
            <>
              <Separator />
              <div className="space-y-2">
                <Label htmlFor="refresh-interval" className="text-sm font-medium">
                  Refresh Interval
                </Label>
                <div className="flex items-center space-x-3">
                  <input
                    id="refresh-interval"
                    type="range"
                    min="5"
                    max="1440"
                    step="5"
                    value={state.refreshInterval}
                    onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
                    className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-sm text-muted-foreground min-w-[80px]">
                    {state.refreshInterval} min
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  How often to collect new data (5 minutes to 24 hours)
                </p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Future Features */}
      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>
            Features planned for future releases
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center space-x-3 text-sm text-muted-foreground">
              <Image className="h-4 w-4" />
              <span>Graph image exports (PNG, SVG)</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-muted-foreground">
              <FileText className="h-4 w-4" />
              <span>PDF report generation</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-muted-foreground">
              <Database className="h-4 w-4" />
              <span>Database export formats</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-muted-foreground">
              <Download className="h-4 w-4" />
              <span>Scheduled export delivery</span>
            </div>
          </div>

          <div className="text-xs text-muted-foreground mt-4 p-3 bg-muted/50 rounded-lg">
            <strong>Feedback Welcome:</strong> Have ideas for export features? 
            Your suggestions help us prioritize development.
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 
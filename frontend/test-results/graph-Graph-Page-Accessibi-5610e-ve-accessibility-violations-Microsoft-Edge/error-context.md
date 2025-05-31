# Test info

- Name: Graph Page Accessibility @accessibility >> should not have accessibility violations
- Location: /Users/arielkalman/GCPHound/frontend/e2e/graph.spec.ts:493:3

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  -    1
+ Received  + 1036

- Array []
+ Array [
+   Object {
+     "description": "Ensure the contrast between foreground and background colors meets WCAG 2 AA minimum contrast ratio thresholds",
+     "help": "Elements must meet minimum color contrast ratio thresholds",
+     "helpUrl": "https://dequeuniversity.com/rules/axe/4.10/color-contrast?application=playwright",
+     "id": "color-contrast",
+     "impact": "serious",
+     "nodes": Array [
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Projects</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".text-card-foreground.border-0.bg-white\\/95:nth-child(1) > .pt-0.p-6 > .space-y-1 > .opacity-50.p-2.hover\\:bg-gray-50:nth-child(1) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">GCP projects</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".text-card-foreground.border-0.bg-white\\/95:nth-child(1) > .pt-0.p-6 > .space-y-1 > .opacity-50.p-2.hover\\:bg-gray-50:nth-child(1) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Service Accounts</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(2) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">Automated service accounts</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(2) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fafafa",
+               "contrastRatio": 3.26,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8b8b8b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">32</div>",
+                 "target": Array [
+                   ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(2) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">32</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(2) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Roles</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(3) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">IAM roles and permissions</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(3) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fafafa",
+               "contrastRatio": 3.26,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8b8b8b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">29</div>",
+                 "target": Array [
+                   ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(3) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">29</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(3) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Custom Roles</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(4) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">Custom IAM roles</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(4) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Users</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(5) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">Human users and accounts</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(5) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fafafa",
+               "contrastRatio": 3.26,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8b8b8b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">63</div>",
+                 "target": Array [
+                   ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(5) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">63</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(5) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Groups</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(6) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">User and service account groups</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(6) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Storage Buckets</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(7) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">Cloud Storage buckets</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(7) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fafafa",
+               "contrastRatio": 3.26,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8b8b8b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">15</div>",
+                 "target": Array [
+                   ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(7) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">15</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(7) > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Compute Instances</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(8) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">Virtual machine instances</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(8) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Cloud Functions</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(9) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(1)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">Serverless functions</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".opacity-50.p-2.hover\\:bg-gray-50:nth-child(9) > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.37,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#888c93",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(2)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.37 (foreground color: #888c93, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs font-medium text-gray-900\">Has Role</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".text-card-foreground.border-0.bg-white\\/95:nth-child(2) > .pt-0.p-6 > .space-y-1 > .opacity-50.p-2.hover\\:bg-gray-50 > .flex-1.space-x-2.flex > .flex-1 > .text-gray-900.font-medium.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.05,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8f949b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"rounded-lg text-card-foreground border-0 shadow-sm bg-white/95 backdrop-blur-sm\">",
+                 "target": Array [
+                   "div[data-testid=\"graph-legend\"] > .text-card-foreground.border-0.bg-white\\/95:nth-child(2)",
+                 ],
+               },
+               Object {
+                 "html": "<div class=\"transition-all duration-300 w-80 
+         overflow-hidden bg-white border-l border-gray-200 z-10\">",
+                 "target": Array [
+                   ".border-l",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.05 (foreground color: #8f949b, background color: #ffffff, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"text-xs text-gray-800\">Has IAM role assignment</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".text-card-foreground.border-0.bg-white\\/95:nth-child(2) > .pt-0.p-6 > .space-y-1 > .opacity-50.p-2.hover\\:bg-gray-50 > .flex-1.space-x-2.flex > .flex-1 > .text-gray-800.text-xs",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#fafafa",
+               "contrastRatio": 3.26,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#8b8b8b",
+               "fontSize": "9.0pt (12px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">175</div>",
+                 "target": Array [
+                   ".text-card-foreground.border-0.bg-white\\/95:nth-child(2) > .pt-0.p-6 > .space-y-1 > .opacity-50.p-2.hover\\:bg-gray-50 > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.26 (foreground color: #8b8b8b, background color: #fafafa, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<div class=\"inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs\">175</div>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".text-card-foreground.border-0.bg-white\\/95:nth-child(2) > .pt-0.p-6 > .space-y-1 > .opacity-50.p-2.hover\\:bg-gray-50 > .flex-1.space-x-2.flex > .bg-secondary.text-secondary-foreground.hover\\:bg-secondary\\/80",
+         ],
+       },
+     ],
+     "tags": Array [
+       "cat.color",
+       "wcag2aa",
+       "wcag143",
+       "TTv5",
+       "TT13.c",
+       "EN-301-549",
+       "EN-9.1.4.3",
+       "ACT",
+     ],
+   },
+ ]
    at /Users/arielkalman/GCPHound/frontend/e2e/graph.spec.ts:500:49
```

# Page snapshot

```yaml
- banner:
  - link "GCPHound Security Dashboard":
    - /url: /
    - img
    - text: GCPHound
    - paragraph: Security Dashboard
  - navigation:
    - link "Dashboard":
      - /url: /
      - img
      - text: Dashboard
    - link "Graph":
      - /url: /graph
      - img
      - text: Graph
    - link "Findings":
      - /url: /findings
      - img
      - text: Findings
    - link "Nodes":
      - /url: /nodes
      - img
      - text: Nodes
    - link "Edges":
      - /url: /edges
      - img
      - text: Edges
    - link "Settings":
      - /url: /settings
      - img
      - text: Settings
  - button "Switch to dark theme":
    - img
  - text: Online
- main:
  - heading "Graph Visualization" [level=1]
  - heading "Search & Filters" [level=2]
  - button "Close search and filters panel":
    - img
  - img
  - textbox "Search nodes by name, ID, or properties..."
  - img
  - text: Filter By 2
  - button "Clear All":
    - img
    - text: Clear All
  - heading "Search & Quick Filters" [level=3]:
    - text: Search & Quick Filters
    - img
  - 'heading "Filter: Node Types" [level=3]':
    - text: "Filter: Node Types"
    - img
  - button "Select All"
  - button "Deselect All"
  - checkbox "Filter by Projects"
  - text: Projects 1
  - checkbox "Filter by Service Accounts"
  - text: Service Accounts 32
  - checkbox "Filter by Roles"
  - text: Roles 29
  - checkbox "Filter by Custom Roles"
  - text: Custom Roles 2
  - checkbox "Filter by Users"
  - text: Users 63
  - checkbox "Filter by Groups"
  - text: Groups 1
  - checkbox "Filter by Storage Buckets"
  - text: Storage Buckets 15
  - checkbox "Filter by Compute Instances"
  - text: Compute Instances 6
  - checkbox "Filter by Cloud Functions"
  - text: Cloud Functions 1
  - 'heading "Filter: Edge Types" [level=3]':
    - text: "Filter: Edge Types"
    - img
  - 'heading "Filter: Risk Levels" [level=3]':
    - text: "Filter: Risk Levels"
    - img
  - checkbox "Filter by Critical risk level" [checked]
  - text: Critical ≥ 80% risk score
  - checkbox "Filter by High risk level" [checked]
  - text: High 60-79% risk score
  - checkbox "Filter by Medium risk level" [checked]
  - text: Medium 40-59% risk score
  - checkbox "Filter by Low risk level" [checked]
  - text: Low 20-39% risk score
  - checkbox "Filter by Info/Safe risk level" [checked]
  - text: Info/Safe < 20% risk score Showing 150 nodes, 498 edges
  - heading "Controls & Legend" [level=2]
  - button "Close controls and legend panel":
    - img
  - text: "Graph Statistics Nodes: 150 Edges: 498 View Controls"
  - button "Zoom In":
    - img
    - text: Zoom In
  - button "Zoom Out":
    - img
    - text: Zoom Out
  - button "Fit to View":
    - img
    - text: Fit to View
  - button "Reset":
    - img
    - text: Reset
  - text: Layout
  - button "Physics On":
    - img
    - text: Physics On
  - button "Force Layout":
    - img
    - text: Force Layout
  - text: Actions
  - button "Export Image":
    - img
    - text: Export Image
  - button "Settings":
    - img
    - text: Settings
  - text: Quick Actions
  - button "🔴 Focus High-Risk"
  - button "⚡ Show Attack Paths"
  - button "🏢 Center Organization"
  - 'heading "Legend: Node Types" [level=3]':
    - text: "Legend: Node Types"
    - img
  - img
  - text: Projects GCP projects 1
  - button "Show":
    - img
  - img
  - text: Service Accounts Automated service accounts 32
  - button "Show":
    - img
  - img
  - text: Roles IAM roles and permissions 29
  - button "Show":
    - img
  - img
  - text: Custom Roles Custom IAM roles 2
  - button "Show":
    - img
  - img
  - text: Users Human users and accounts 63
  - button "Show":
    - img
  - img
  - text: Groups User and service account groups 1
  - button "Show":
    - img
  - img
  - text: Storage Buckets Cloud Storage buckets 15
  - button "Show":
    - img
  - img
  - text: Compute Instances Virtual machine instances 6
  - button "Show":
    - img
  - img
  - text: Cloud Functions Serverless functions 1
  - button "Show":
    - img
  - 'heading "Legend: Edge Types" [level=3]':
    - text: "Legend: Edge Types"
    - img
  - text: Has Role Has IAM role assignment 175
  - button "Show":
    - img
  - 'heading "Legend: Risk Levels" [level=3]':
    - text: "Legend: Risk Levels"
    - img
  - text: Critical Risk ≥ 80% risk score - Immediate action required High Risk 60-79% risk score - Should be addressed soon Medium Risk 40-59% risk score - Review and plan remediation Low Risk 20-39% risk score - Monitor Info/Safe < 20% risk score - Low priority
```

# Test source

```ts
  400 |         }
  401 |         
  402 |         route.fulfill({
  403 |           status: 200,
  404 |           contentType: 'application/json',
  405 |           body: JSON.stringify({
  406 |             nodes,
  407 |             edges,
  408 |             metadata: {
  409 |               total_nodes: nodes.length,
  410 |               total_edges: edges.length,
  411 |               collection_time: new Date().toISOString(),
  412 |               gcp_projects: ['large-project']
  413 |             }
  414 |           })
  415 |         });
  416 |       });
  417 |       
  418 |       await page.goto('/graph');
  419 |       
  420 |       // Should load within reasonable time
  421 |       await page.waitForSelector('[data-testid="graph-canvas"]', { timeout: 30000 });
  422 |       
  423 |       // Should still be responsive
  424 |       const zoomButton = page.getByRole('button', { name: /zoom in/i });
  425 |       await zoomButton.click();
  426 |       
  427 |       // Should not show performance warnings or errors
  428 |       const errorMessage = page.getByText(/error|warning/i);
  429 |       await expect(errorMessage).not.toBeVisible();
  430 |     });
  431 |
  432 |     test('should load within performance budget', async ({ page }) => {
  433 |       const startTime = Date.now();
  434 |       
  435 |       await page.goto('/graph');
  436 |       await page.waitForSelector('[data-testid="graph-canvas"]');
  437 |       
  438 |       const loadTime = Date.now() - startTime;
  439 |       
  440 |       // Should load within 10 seconds
  441 |       expect(loadTime).toBeLessThan(10000);
  442 |     });
  443 |   });
  444 |
  445 |   test.describe('Error Handling', () => {
  446 |     test('should handle API errors gracefully', async ({ page }) => {
  447 |       await page.route('**/api/graph', route => route.abort('failed'));
  448 |       
  449 |       await page.goto('/graph');
  450 |       
  451 |       // Should show error message
  452 |       await expect(page.getByText(/error|failed/i)).toBeVisible();
  453 |       
  454 |       // Should still show basic layout
  455 |       await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
  456 |     });
  457 |
  458 |     test('should handle empty graph data', async ({ page }) => {
  459 |       await page.route('**/api/graph', route => {
  460 |         route.fulfill({
  461 |           status: 200,
  462 |           contentType: 'application/json',
  463 |           body: JSON.stringify({
  464 |             nodes: [],
  465 |             edges: [],
  466 |             metadata: {
  467 |               total_nodes: 0,
  468 |               total_edges: 0,
  469 |               collection_time: new Date().toISOString(),
  470 |               gcp_projects: []
  471 |             }
  472 |           })
  473 |         });
  474 |       });
  475 |       
  476 |       await page.goto('/graph');
  477 |       
  478 |       // Should show empty state message
  479 |       await expect(page.getByText(/no data|empty/i)).toBeVisible();
  480 |       
  481 |       // Graph controls should still be available
  482 |       await expect(page.getByTestId('graph-controls')).toBeVisible();
  483 |     });
  484 |   });
  485 | });
  486 |
  487 | test.describe('Graph Page Accessibility @accessibility', () => {
  488 |   test.beforeEach(async ({ page }) => {
  489 |     await setupGraphData(page);
  490 |     await page.goto('/graph');
  491 |   });
  492 |
  493 |   test('should not have accessibility violations', async ({ page }) => {
  494 |     await page.waitForSelector('[data-testid="graph-canvas"]');
  495 |     
  496 |     const accessibilityScanResults = await new AxeBuilder({ page })
  497 |       .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
  498 |       .analyze();
  499 |
> 500 |     expect(accessibilityScanResults.violations).toEqual([]);
      |                                                 ^ Error: expect(received).toEqual(expected) // deep equality
  501 |   });
  502 |
  503 |   test('should have accessible controls', async ({ page }) => {
  504 |     await page.waitForSelector('[data-testid="graph-controls"]');
  505 |     
  506 |     // All buttons should have accessible names
  507 |     const buttons = page.locator('[data-testid="graph-controls"] button');
  508 |     const count = await buttons.count();
  509 |     
  510 |     for (let i = 0; i < count; i++) {
  511 |       const button = buttons.nth(i);
  512 |       const accessibleName = await button.getAttribute('aria-label') || await button.textContent();
  513 |       expect(accessibleName?.trim()).toBeTruthy();
  514 |     }
  515 |   });
  516 |
  517 |   test('should support keyboard navigation', async ({ page }) => {
  518 |     await page.waitForSelector('[data-testid="graph-controls"]');
  519 |     
  520 |     // Should be able to tab through controls
  521 |     await page.keyboard.press('Tab');
  522 |     const focusedElement = await page.locator(':focus').first();
  523 |     await expect(focusedElement).toBeVisible();
  524 |     
  525 |     // Should be able to activate with Enter or Space
  526 |     await page.keyboard.press('Enter');
  527 |     
  528 |     // Should not cause errors
  529 |     const errorMessage = page.getByText(/error/i);
  530 |     await expect(errorMessage).not.toBeVisible();
  531 |   });
  532 |
  533 |   test('should have accessible panels', async ({ page }) => {
  534 |     // Open a panel
  535 |     await page.evaluate(() => {
  536 |       window.dispatchEvent(new CustomEvent('nodeSelected', {
  537 |         detail: {
  538 |           nodeId: 'user:test@example.com',
  539 |           nodeData: {
  540 |             id: 'user:test@example.com',
  541 |             type: 'user',
  542 |             name: 'test@example.com',
  543 |             properties: { email: 'test@example.com', riskScore: 0.8 }
  544 |           }
  545 |         }
  546 |       }));
  547 |     });
  548 |     
  549 |     await expect(page.getByTestId('node-detail-panel')).toBeVisible();
  550 |     
  551 |     // Panel should have proper heading
  552 |     const heading = page.locator('[data-testid="node-detail-panel"] h1, [data-testid="node-detail-panel"] h2');
  553 |     await expect(heading.first()).toBeVisible();
  554 |     
  555 |     // Close button should be accessible
  556 |     const closeButton = page.getByRole('button', { name: /close/i });
  557 |     await expect(closeButton).toBeVisible();
  558 |     await expect(closeButton).toBeFocused();
  559 |   });
  560 | }); 
```
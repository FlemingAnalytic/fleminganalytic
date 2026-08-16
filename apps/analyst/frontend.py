# Smart Analyst v2.0 - Frontend HTML Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Analyst v2</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/axios/1.6.2/axios.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        .loader { width: 24px; height: 24px; border: 3px solid #e5e7eb; border-top-color: #4F46E5; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .tab-active { background: #4F46E5; color: white; }
        .main-tab-active-data { background: #4F46E5 !important; color: white !important; shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
        .main-tab-active-analysis { background: #059669 !important; color: white !important; shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
        .main-tab-active-modeling { background: #7C3AED !important; color: white !important; shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
        .insight-card { transition: all 0.2s; }
        .step-active { border-color: #4F46E5; background: #EEF2FF; color: #4F46E5; }
        .step-todo { border-color: #E5E7EB; color: #9CA3AF; }
        .step-done { border-color: #10B981; background: #ECFDF5; color: #059669; }
        .insight-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .pivot-table { font-size: 12px; }
        .pivot-table th { background: #F1F5F9; position: sticky; top: 0; z-index: 10; }
        .pivot-table td, .pivot-table th { padding: 8px 12px; border: 1px solid #E2E8F0; }
        .pivot-table tr:hover { background: #F8FAFC; }
        .question-btn { transition: all 0.15s; }
        .question-btn:hover { background: #EEF2FF; border-color: #4F46E5; }
        .filter-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; min-width: 180px; }
        .feature-item:hover { background: #f3f4f6; }
        .feature-item input:checked + label { color: #4F46E5; font-weight: 500; }



        .quick-filter-btn { transition: all 0.15s ease; }
        .quick-filter-btn.active { background-color: #4F46E5; color: white; border-color: #4F46E5; }

        #previewTable th { position: sticky; top: 0; background: #f9fafb; z-index: 10; }
        #previewTable td { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        #previewTable tr:hover td { white-space: normal; word-break: break-all; }

        @media print {
            * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
            body { background: white !important; font-size: 11pt; }
            header, #uploadSection, #loadingOverlay, button:not(.print-include), #filtersContainer, select, input, .no-print { display: none !important; }
            #modelingSection { display: block !important; }
            #analysisSection, #analysisAccordionContent, #modelAccordionContent { display: block !important; }
            #view-summary, #view-overview, #view-classify, #view-pivot, #view-visualize { display: block !important; }
            .inline-flex.gap-1, .bg-gray-100.rounded-xl.p-1 { display: none !important; }
            @page { size: A4; margin: 0.75in; }
            #view-overview, #view-classify, #view-pivot, #view-visualize { page-break-before: always !important; }
            #view-preview { display: none !important; }
            #view-summary { page-break-before: avoid !important; }
            .insight-card, .bg-white.rounded-xl, .grid > div, tr { page-break-inside: avoid; }
            .pivot-table { font-size: 9pt; width: 100%; }
            #aiSummaryContainer { background: #F9FAFB !important; border: 1px solid #E5E7EB !important; display: block !important; }
        }

        #mobileWarning { display: none; }
        @media only screen and (max-width: 1024px) {
            #mobileWarning { 
                display: flex !important; 
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: white; z-index: 9999; flex-direction: column; 
                align-items: center; justify-content: center; text-align: center; padding: 2rem;
            }
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div id="mobileWarning" class="no-print">
        <div class="max-w-md">
            <div class="w-16 h-16 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
            </div>
            <h2 class="text-2xl font-bold text-gray-900 mb-2">Desktop Browser Required</h2>
            <p class="text-gray-600 mb-8">Smart Analyst features complex data visualizations and modeling tools designed for full-size displays. Please switch to a laptop or desktop for the best experience.</p>
            <button onclick="document.getElementById('mobileWarning').style.display='none'" class="text-indigo-600 font-semibold hover:text-indigo-700">Continue anyway (not recommended)</button>
        </div>
    </div>
    <div id="loadingOverlay" class="fixed inset-0 bg-black/50 z-50 hidden items-center justify-center">
        <div class="bg-white rounded-2xl p-8 flex flex-col items-center gap-4">
            <div class="loader"></div>
            <p class="text-gray-600" id="loadingText">Processing...</p>
        </div>
    </div>

    <header class="bg-white border-b sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                        </svg>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-gray-900">Smart Analyst</h1>
                        <p class="text-sm text-gray-500">Intelligent Data Analysis</p>
                    </div>
                </div>
                <div id="datasetInfo" class="hidden flex items-center gap-4">

                    <div class="text-right">
                        <p class="text-sm font-medium text-gray-900" id="currentDataset">-</p>
                        <p class="text-xs text-gray-500" id="datasetSize">-</p>
                    </div>
                    <button onclick="resetAnalysis()" class="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg">
                        Change Dataset
                    </button>
                    <button onclick="window.print()" class="px-3 py-2 text-sm bg-gray-900 text-white rounded-lg flex items-center gap-1 hover:bg-gray-800 transition-colors">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
                        </svg>
                        Print PDF
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Guided Workflow Banner -->
    <div class="max-w-7xl mx-auto px-4 mt-6 no-print">
        <div class="bg-white rounded-2xl p-4 shadow-sm border flex items-center justify-between">
            <div class="flex items-center gap-6 overflow-x-auto pb-2 md:pb-0">
                <button onclick="showSection('upload')" id="step1" class="flex items-center gap-2 px-3 py-1.5 rounded-xl border-2 text-xs font-bold uppercase tracking-wider transition-all step-active cursor-pointer hover:opacity-80">
                    <span class="w-5 h-5 rounded-full border-2 border-current flex items-center justify-center">1</span>
                    Load Data
                </button>
                <div class="h-px w-8 bg-gray-200 hidden md:block"></div>
                <button onclick="showSection('analysis')" id="step2" class="flex items-center gap-2 px-3 py-1.5 rounded-xl border-2 text-xs font-bold uppercase tracking-wider transition-all step-todo cursor-pointer hover:opacity-80">
                    <span class="w-5 h-5 rounded-full border-2 border-current flex items-center justify-center">2</span>
                    Analyze Patterns
                </button>
                <div class="h-px w-8 bg-gray-200 hidden md:block"></div>
                <button onclick="showSection('modeling')" id="step3" class="flex items-center gap-2 px-3 py-1.5 rounded-xl border-2 text-xs font-bold uppercase tracking-wider transition-all step-todo cursor-pointer hover:opacity-80">
                    <span class="w-5 h-5 rounded-full border-2 border-current flex items-center justify-center">3</span>
                    Predict Results
                </button>
            </div>
            <div id="guideText" class="hidden md:flex items-center gap-2 text-sm text-gray-500 italic">
                <svg class="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span>Ready to start? Load a datasheet above.</span>
            </div>
        </div>
    </div>

    <!-- Global Notification Container -->
    <div id="noticeContainer" class="max-w-7xl mx-auto px-4 mt-4 space-y-2 no-print"></div>

    <!-- Main Navigation Bar -->
    <nav id="mainNav" class="max-w-7xl mx-auto px-4 mt-6 hidden no-print">
        <div class="flex gap-2 p-1.5 bg-white rounded-2xl shadow-sm border w-fit">
            <button onclick="showSection('upload')" class="main-tab-btn px-6 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2" data-section="upload">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                Data Source
            </button>
            <button onclick="showSection('analysis')" class="main-tab-btn px-6 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2" data-section="analysis">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                Analysis Tools
            </button>
            <button onclick="showSection('modeling')" class="main-tab-btn px-6 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2" data-section="modeling">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                Predictive AI
            </button>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- Upload Section -->
        <section id="uploadSection" class="mb-8">
            <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
                <div class="w-full px-6 py-4 flex items-center justify-between border-b">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                            </svg>
                        </div>
                        <span class="font-semibold text-gray-900">Load Data Source</span>
                    </div>
                </div>

                <div id="dataAccordionContent" class="px-6 pb-6">
                    <div class="grid md:grid-cols-3 gap-6">
                        <!-- File Upload -->
                        <div class="space-y-3">
                            <h3 class="font-medium text-gray-700 flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                                </svg>
                                Upload File
                            </h3>
                            <div class="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center hover:border-indigo-400 transition-colors cursor-pointer" onclick="document.getElementById('fileInput').click()">
                                <input type="file" id="fileInput" class="hidden" accept=".csv,.xlsx,.xls,.json" onchange="handleFileUpload(event)">
                                <p class="text-sm text-gray-500">Drop CSV, Excel, or JSON</p>
                                <p class="text-xs text-gray-400 mt-1">or click to browse</p>
                            </div>
                        </div>

                        <!-- URL Load -->
                        <div class="space-y-3">
                            <h3 class="font-medium text-gray-700 flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                                </svg>
                                Load from URL
                                <span class="text-xs text-gray-400">(CSV, Excel, JSON)</span>
                            </h3>
                            <div class="flex flex-col gap-2">
                                <input type="text" id="urlInput" placeholder="https://example.com/data.csv" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                                <button onclick="loadFromUrl()" class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 shadow-sm transition-all">Load from URL</button>
                            </div>
                            <div class="text-xs text-gray-500">
                                <span class="font-medium">Try these:</span>
                                <div class="flex flex-wrap gap-1 mt-1">
                                    <button onclick="loadExampleUrl('ev')" class="px-2 py-0.5 bg-gray-100 hover:bg-indigo-100 hover:text-indigo-700 rounded text-xs transition-colors">Electric Vehicles</button>
                                    <button onclick="loadExampleUrl('airline')" class="px-2 py-0.5 bg-gray-100 hover:bg-indigo-100 hover:text-indigo-700 rounded text-xs transition-colors">Airline Safety</button>
                                    <button onclick="loadExampleUrl('covid')" class="px-2 py-0.5 bg-gray-100 hover:bg-indigo-100 hover:text-indigo-700 rounded text-xs transition-colors">COVID US States</button>
                                    <button onclick="loadExampleUrl('gold')" class="px-2 py-0.5 bg-gray-100 hover:bg-indigo-100 hover:text-indigo-700 rounded text-xs transition-colors">Gold Prices</button>
                                    <button onclick="loadExampleUrl('oil')" class="px-2 py-0.5 bg-gray-100 hover:bg-indigo-100 hover:text-indigo-700 rounded text-xs transition-colors">Oil Prices</button>
                                    <button onclick="loadExampleUrl('majors')" class="px-2 py-0.5 bg-gray-100 hover:bg-indigo-100 hover:text-indigo-700 rounded text-xs transition-colors">College Majors</button>
                                </div>
                            </div>
                            <div class="text-xs text-gray-400 pt-1 border-t">
                                Find more:
                                <a href="https://github.com/awesomedata/awesome-public-datasets" target="_blank" class="text-indigo-500 hover:underline">Awesome Public Datasets</a> |
                                <a href="https://www.kaggle.com/datasets" target="_blank" class="text-indigo-500 hover:underline">Kaggle</a> |
                                <a href="https://datasetsearch.research.google.com/" target="_blank" class="text-indigo-500 hover:underline">Google Dataset Search</a>
                            </div>
                        </div>

                        <!-- Sample Datasets -->
                        <div class="space-y-3">
                            <h3 class="font-medium text-gray-700 flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                                </svg>
                                Sample Datasets
                            </h3>
                            <div class="space-y-2">
                                <select id="savedDataSelect" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500">
                                    <option value="">Custom Data...</option>
                                </select>
                                <select id="publicDatasetSelect" class="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500">
                                    <option value="">Public datasets...</option>
                                <optgroup label="Classic ML & Samples">
                                    <option value="titanic">Titanic Survival (891 rows)</option>
                                    <option value="tips">Restaurant Tips (244 rows)</option>
                                    <option value="iris">Iris Flowers (150 rows)</option>
                                    <option value="penguins">Penguins (344 rows)</option>
                                    <option value="diamonds">Diamonds (54K rows)</option>
                                    <option value="mpg">Auto MPG (398 rows)</option>
                                    <option value="car_crashes">US Car Crashes</option>
                                </optgroup>
                                <optgroup label="Crime & Urban Analytics">
                                    <option value="nyc_311_calls">NYC 311 Service Requests (100K)</option>
                                    <option value="chicago_crimes">Chicago Crime Data (100K)</option>
                                    <option value="la_crimes">LA Crime Data (100K)</option>
                                    <option value="nyc_motor_collisions">NYC Traffic Collisions (100K)</option>
                                </optgroup>
                                <optgroup label="Economics & Finance">
                                    <option value="lending_club">Lending Club Loans (100K)</option>
                                    <option value="us_county_economics">US County Economy</option>
                                    <option value="sp500_companies">S&P 500 Companies</option>
                                    <option value="online_retail">UK Online Retail (541K)</option>
                                    <option value="instacart_orders">Instacart Orders (100K)</option>
                                </optgroup>
                                <optgroup label="Health & Demographics">
                                    <option value="sk_breast_cancer">Breast Cancer Diagnostic</option>
                                    <option value="sk_diabetes">Diabetes Scenarios</option>
                                    <option value="covid_us_counties">COVID-19 US Counties (2M+)</option>
                                    <option value="medicare_spending">Medicare Spending</option>
                                    <option value="world_happiness">World Happiness Report</option>
                                    <option value="us_baby_names">US Baby Names (2M)</option>
                                </optgroup>
                                <optgroup label="Science & Environment">
                                    <option value="planets">Exoplanets (1K rows)</option>
                                    <option value="geyser">Old Faithful Geyser</option>
                                    <option value="global_power_plants">Global Power Plants</option>
                                    <option value="us_wildfires">US Wildfires (88K)</option>
                                </optgroup>
                                <optgroup label="Sports & Entertainment">
                                    <option value="nba_shots">NBA Shot Charts (128K)</option>
                                    <option value="spotify_tracks">Spotify Track Features (114K)</option>
                                    <option value="video_game_sales">Video Game Sales (16K)</option>
                                </optgroup>
                                <optgroup label="Travel & Tech">
                                    <option value="airbnb_nyc">NYC Airbnb Listings (49K)</option>
                                    <option value="flight_delays">US Flight Delays (100K)</option>
                                    <option value="github_repos">GitHub Repo Specs (50K)</option>
                                    <option value="stackoverflow_survey">StackOverflow Survey (65K)</option>
                                </optgroup>
                                <optgroup label="US Census Bureau API (Direct)">
                                    <option value="census_national_demographics">US National Demographics</option>
                                    <option value="census_state_demographics">US States Demographics</option>
                                    <option value="census_county_demographics">US Counties Demographics</option>
                                    <option value="census_zip_demographics">US Zip Codes (ZCTA) Demographics</option>
                                    <option value="census_county_pop">County Pop Growth (2020-23)</option>
                                    <option value="census_state_pop">State Pop Growth (2020-23)</option>
                                    <option value="census_county_economics">US County Economy</option>
                                </optgroup>
                                <optgroup label="Retail & Local">
                                    <option value="us_car_dealerships">US Car Dealerships (19K)</option>
                                </optgroup>
                                <optgroup label="Asset-Backed Securities (SEC ABS-EE)">
                                    <option value="abs_auto_loans">ABS Auto Loans - Loan Level (100K)</option>
                                    <option value="abs_auto_leases">ABS Auto Leases - Lease Level (100K)</option>
                                    <option value="abs_cmbs_loans">ABS CMBS - Commercial Loans (46K)</option>
                                    <option value="abs_cmbs_properties">ABS CMBS - Properties &amp; Tenants (64K)</option>
                                </optgroup>
                                </select>
                                <button onclick="loadManualDataset()" class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 shadow-sm transition-all">Load Dataset</button>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </section>

        <!-- Analysis Section -->
        <section id="analysisSection" class="hidden">
            <div class="bg-white rounded-2xl shadow-sm border overflow-hidden mb-6">
                <div class="w-full px-6 py-4 flex items-center justify-between border-b">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                            <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                            </svg>
                        </div>
                        <span class="font-semibold text-gray-900">Analysis Tools</span>
                    </div>
                </div>

                <div id="analysisAccordionContent" class="px-6 pb-6">
                    <!-- Tabs -->
                    <div class="flex items-center justify-between mb-6">
                        <div class="inline-flex gap-1 bg-gray-100 rounded-xl p-1">
                            <button onclick="showTab('summary')" class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors tab-active" data-tab="summary">Summary</button>
                            <button onclick="showTab('preview')" class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors" data-tab="preview">Preview</button>
                            <button onclick="showTab('overview')" class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors" data-tab="overview">Columns</button>
                            <button onclick="showTab('classify')" class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors" data-tab="classify">Classify</button>
                            <button onclick="showTab('pivot')" class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors" data-tab="pivot">Pivot</button>
                            <button onclick="showTab('visualize')" class="tab-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors" data-tab="visualize">Visualize</button>
                        </div>

                        <div class="flex gap-2">
                            <button onclick="exportData('csv')" class="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg flex items-center gap-1">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                                Export CSV
                            </button>
                            <button onclick="window.print()" class="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg flex items-center gap-1">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
                                </svg>
                                Print Report
                            </button>
                        </div>
                    </div>

                    <!-- Tab Content -->
                    <div id="view-summary" class="tab-content">
                        <div id="enrichmentResults" class="mb-6 hidden"></div>
                        <div class="grid md:grid-cols-2 gap-6">
                            <div>
                                <h3 class="font-semibold text-gray-900 mb-4">Key Insights</h3>
                                <div id="insightsContainer" class="space-y-3"></div>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-900 mb-4">Suggested Questions</h3>
                                <div id="questionsContainer" class="space-y-2"></div>
                            </div>
                        </div>
                    </div>

                    <div id="view-preview" class="tab-content hidden">
                        <div class="overflow-x-auto max-h-96">
                            <table id="previewTable" class="w-full text-sm">
                                <thead id="previewHead"></thead>
                                <tbody id="previewBody"></tbody>
                            </table>
                        </div>
                    </div>

                    <div id="view-overview" class="tab-content hidden">
                        <div id="columnsContainer" class="grid md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
                    </div>

                    <div id="view-classify" class="tab-content hidden">
                        <div class="grid md:grid-cols-2 gap-6">
                            <div class="space-y-4">
                                <h3 class="font-semibold text-gray-900">Create Classification</h3>
                                <div>
                                    <label class="block text-sm text-gray-600 mb-1">Source Column</label>
                                    <select id="classifyColumn" class="w-full px-3 py-2 border rounded-lg"></select>
                                </div>
                                <div>
                                    <label class="block text-sm text-gray-600 mb-1">Method</label>
                                    <select id="classifyMethod" class="w-full px-3 py-2 border rounded-lg">
                                        <option value="quintiles">Quintiles (5 groups)</option>
                                        <option value="quartiles">Quartiles (4 groups)</option>
                                        <option value="deciles">Deciles (10 groups)</option>
                                        <option value="statistical">Statistical (z-score)</option>
                                        <option value="kmeans">K-Means Clustering</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-sm text-gray-600 mb-1">New Column Name</label>
                                    <input type="text" id="classifyName" class="w-full px-3 py-2 border rounded-lg" placeholder="e.g., income_tier">
                                </div>
                                <button onclick="createClassification()" class="w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Create Classification</button>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-900 mb-4">Active Classifications</h3>
                                <div id="classificationsContainer" class="space-y-3"></div>
                            </div>
                        </div>
                    </div>

                    <div id="view-pivot" class="tab-content hidden">
                        <div class="grid md:grid-cols-4 gap-4 mb-6">
                            <div>
                                <label class="block text-sm text-gray-600 mb-1">Row Dimension</label>
                                <select id="pivotRows" class="w-full px-3 py-2 border rounded-lg"></select>
                            </div>
                            <div>
                                <label class="block text-sm text-gray-600 mb-1">Column Dimension (optional)</label>
                                <select id="pivotCols" class="w-full px-3 py-2 border rounded-lg">
                                    <option value="">None</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm text-gray-600 mb-1">Value</label>
                                <select id="pivotValues" class="w-full px-3 py-2 border rounded-lg"></select>
                            </div>
                            <div>
                                <label class="block text-sm text-gray-600 mb-1">Aggregation</label>
                                <select id="pivotAgg" class="w-full px-3 py-2 border rounded-lg" onchange="toggleWeightColumn()">
                                    <option value="sum">Sum</option>
                                    <option value="mean">Average</option>
                                    <option value="wtd_avg">Weighted Avg</option>
                                    <option value="count">Count</option>
                                    <option value="median">Median</option>
                                    <option value="min">Min</option>
                                    <option value="max">Max</option>
                                </select>
                            </div>
                        </div>
                        <div id="pivotWeightContainer" class="mb-6 hidden">
                            <label class="block text-sm text-gray-600 mb-1">Weight Column (for Weighted Avg: sum(weight × value) / sum(weight))</label>
                            <select id="pivotWeightCol" class="w-full md:w-1/4 px-3 py-2 border rounded-lg"></select>
                        </div>
                        <button onclick="createPivot()" class="mb-6 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Generate Pivot Table</button>
                        <div id="pivotResult" class="overflow-x-auto"></div>
                    </div>

                    <div id="view-visualize" class="tab-content hidden">
                        <div class="grid md:grid-cols-4 gap-4 mb-6">
                            <div>
                                <label class="block text-sm text-gray-600 mb-1">Chart Type</label>
                                <select id="vizType" class="w-full px-3 py-2 border rounded-lg" onchange="updateVizOptions()">
                                    <option value="correlation">Correlation Heatmap</option>
                                    <option value="distribution">Distribution</option>
                                    <option value="scatter">Scatter Plot</option>
                                    <option value="bar">Bar Chart</option>
                                    <option value="cluster">Cluster Plot</option>
                                    <option value="map">Interactive Geo Map</option>
                                </select>
                            </div>
                            <div id="vizXContainer">
                                <label class="block text-sm text-gray-600 mb-1">X Axis / Column</label>
                                <select id="vizX" class="w-full px-3 py-2 border rounded-lg"></select>
                            </div>
                            <div id="vizYContainer" class="hidden">
                                <label class="block text-sm text-gray-600 mb-1">Y Axis</label>
                                <select id="vizY" class="w-full px-3 py-2 border rounded-lg"></select>
                            </div>
                            <div id="vizColorContainer" class="hidden">
                                <label class="block text-sm text-gray-600 mb-1">Color By</label>
                                <select id="vizColor" class="w-full px-3 py-2 border rounded-lg">
                                    <option value="">None</option>
                                </select>
                            </div>
                        </div>
                        <button onclick="createVisualization()" class="mb-6 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Generate Chart</button>
                        <div id="vizResult" class="flex justify-center"></div>
                    </div>


                </div>
            </div>
        </section>

        <!-- Modeling Section -->
        <section id="modelingSection" class="hidden">
            <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
                <div class="w-full px-6 py-4 flex items-center justify-between border-b">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                            <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                            </svg>
                        </div>
                        <span class="font-semibold text-gray-900">Predictive AI Modeling</span>
                    </div>
                </div>

                <div id="modelAccordionContent" class="px-6 pb-6 mt-6">
                    <div class="grid md:grid-cols-2 gap-6">
                        <div class="space-y-4">
                            <h3 class="font-semibold text-gray-900">1. Setup Your Prediction</h3>
                            <div>
                                <label class="block text-sm text-gray-600 mb-1 font-medium italic">"What would you like the AI to predict?"</label>
                                <select id="modelTarget" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500" onchange="populateFeatureSelector()"></select>
                            </div>

                            <!-- New Feature Selector -->
                            <div class="space-y-2">
                                <label class="block text-sm text-gray-600 font-medium italic">"What information should the AI look at to make its guess?"</label>
                                <div class="border rounded-xl bg-white overflow-hidden shadow-sm">
                                    <div class="px-3 py-2 border-b bg-gray-50 flex items-center justify-between">
                                        <div class="flex items-center gap-2">
                                            <input type="checkbox" id="selectAllFeatures" onchange="toggleAllFeatures(this.checked)" class="rounded text-indigo-600 focus:ring-indigo-500">
                                            <label for="selectAllFeatures" class="text-xs font-bold text-gray-700 uppercase tracking-tighter">Select All</label>
                                        </div>
                                        <div class="relative">
                                            <input type="text" id="featureSearch" oninput="filterFeatureList(this.value)" placeholder="Search..." class="text-xs py-1 pl-2 pr-6 border rounded-lg bg-white focus:ring-1 focus:ring-indigo-500 w-32">
                                            <svg class="w-3 h-3 absolute right-2 top-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                                        </div>
                                    </div>
                                    <div id="allFeaturesList" class="max-h-60 overflow-y-auto p-2 space-y-0.5 custom-scrollbar">
                                        <!-- Populated dynamically -->
                                    </div>
                                </div>
                            </div>

                            <button onclick="analyzeFeatures()" class="w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all flex items-center justify-center gap-2 shadow-sm">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                Smart Select (AI Choice)
                            </button>
                            <div id="featureImportanceResult"></div>
                            <div id="trainModelSection" class="hidden space-y-4 pt-4 border-t">
                                <h3 class="font-semibold text-gray-900">2. Generate the AI Brain</h3>
                                <div>
                                    <label class="block text-sm text-gray-600 mb-1 font-medium">Currently Selected Features:</label>
                                    <div id="selectedFeatures" class="flex flex-wrap gap-2 min-h-[40px] p-2 bg-gray-50 rounded-lg border border-dashed"></div>
                                </div>
                                <div>
                                    <label class="block text-sm text-gray-600 mb-1">Model Type</label>
                                    <select id="modelType" class="w-full px-3 py-2 border rounded-lg">
                                        <option value="auto">Auto-Select (Best Fit)</option>
                                        <option value="random_forest">Random Forest</option>
                                        <option value="gradient_boosting">Gradient Boosting</option>
                                        <option value="linear_regression">Linear Regression (LINEST Style)</option>
                                    </select>
                                </div>
                                <button onclick="trainModel()" class="w-full py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">Train Model</button>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-semibold text-gray-900 mb-4">Model Results</h3>
                            <div id="modelResults"></div>
                            
                             <!-- AI Executive Summary -->
                             <div id="aiSummaryContainer" class="hidden mt-4 bg-indigo-50 rounded-2xl border border-indigo-100 shadow-sm overflow-hidden">
                                 <button onclick="toggleAiSummary()" class="w-full p-4 flex items-center justify-between hover:bg-indigo-100/50 transition-colors">
                                     <h4 class="font-bold text-indigo-900 flex items-center gap-2">
                                         <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                                         </svg>
                                         AI Executive Summary
                                     </h4>
                                     <span id="aiSummaryArrow" class="text-indigo-400 font-bold text-xl">+</span>
                                 </button>
                                 <div id="aiSummaryContent" class="hidden px-5 pb-5 border-t border-indigo-100/30 pt-4">
                                     <div id="aiSummary" class="text-sm text-indigo-900 leading-relaxed italic space-y-2">
                                         <div class="flex items-center gap-2">
                                             <div class="loader w-4 h-4 border-2"></div>
                                             <span>Thinking...</span>
                                         </div>
                                     </div>
                                 </div>
                             </div>

                            <div id="predictionForm" class="hidden mt-6 space-y-4">
                                <h4 class="font-medium text-gray-800">Make Predictions</h4>
                                <div id="predictionInputs"></div>
                                <button onclick="makePrediction()" class="w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Predict</button>
                                <div id="predictionResult"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <script>
        // Global state
        let currentFilename = null;
        let currentProfile = null;
        let classifications = {};
        let selectedFeatures = [];
        let modelFormFields = [];

        // API base URL - adjust for the router prefix
        const API_BASE = window.location.pathname.replace(/\\/$/, '');

        // Show Global Notice
        function showNotice(title, message, type = 'info') {
            const container = document.getElementById('noticeContainer');
            const icons = {
                info: '<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
                warning: '<svg class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
                success: '<svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
                error: '<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
            };
            
            const bgClasses = {
                info: 'bg-blue-50 border-blue-100',
                warning: 'bg-yellow-50 border-yellow-100',
                success: 'bg-green-50 border-green-100',
                error: 'bg-red-50 border-red-100'
            };

            const notice = document.createElement('div');
            notice.className = `flex items-center justify-between p-3 rounded-xl border shadow-sm animate-all transition-all ${bgClasses[type]}`;
            notice.innerHTML = `
                <div class="flex items-center gap-3">
                    ${icons[type]}
                    <div class="flex flex-col">
                        <span class="text-xs font-bold uppercase tracking-wider text-gray-900 leading-tight">${title}</span>
                        <span class="text-sm text-gray-700 leading-tight">${message}</span>
                    </div>
                </div>
                <button onclick="this.parentElement.remove()" class="text-gray-400 hover:text-gray-600 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            `;
            container.appendChild(notice);
            
            // Auto hide after 10 seconds unless it's an error
            if (type !== 'error') {
                setTimeout(() => notice.remove(), 10000);
            }
        }

        // Loading overlay
        function showLoading(text = 'Processing...') {
            document.getElementById('loadingText').textContent = text;
            document.getElementById('loadingOverlay').classList.remove('hidden');
            document.getElementById('loadingOverlay').classList.add('flex');
        }

        function hideLoading() {
            document.getElementById('loadingOverlay').classList.add('hidden');
            document.getElementById('loadingOverlay').classList.remove('flex');
        }



        // File upload
        async function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            showLoading('Uploading and analyzing...');
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await axios.post(`${API_BASE}/upload`, formData);
                handleDataLoaded(response.data);
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Example dataset URLs
        const exampleUrls = {
            'ev': 'https://raw.githubusercontent.com/fivethirtyeight/data/master/ev-charging/ev_data.csv',
            'airline': 'https://raw.githubusercontent.com/fivethirtyeight/data/master/airline-safety/airline-safety.csv',
            'covid': 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv',
            'gold': 'https://raw.githubusercontent.com/datasets/gold-prices/master/data/monthly.csv',
            'oil': 'https://raw.githubusercontent.com/datasets/oil-prices/master/data/brent-monthly.csv',
            'majors': 'https://raw.githubusercontent.com/fivethirtyeight/data/master/college-majors/recent-grads.csv'
        };

        // Load example URL
        function loadExampleUrl(key) {
            const url = exampleUrls[key];
            if (url) {
                document.getElementById('urlInput').value = url;
                loadFromUrl();
            }
        }

        // Load from URL
        async function loadFromUrl() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) return alert('Please enter a URL');

            showLoading('Loading from URL...');
            const formData = new FormData();
            formData.append('url', url);

            try {
                const response = await axios.post(`${API_BASE}/load-url`, formData);
                handleDataLoaded(response.data);
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Load public dataset
        async function loadPublicDataset() {
            const name = document.getElementById('publicDatasetSelect').value;
            if (!name) return;

            showLoading('Loading dataset...');
            const formData = new FormData();
            formData.append('name', name);

            try {
                const response = await axios.post(`${API_BASE}/load-public`, formData);
                handleDataLoaded(response.data);
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Populate saved datasets dropdown on page load
        async function populateSavedDatasets() {
            try {
                const response = await axios.get(`${API_BASE}/saved-datasets`);
                const select = document.getElementById('savedDataSelect');
                const datasets = response.data.datasets || [];

                // Keep the default option and add datasets
                select.innerHTML = '<option value="">Custom Data...</option>';
                datasets.forEach(ds => {
                    const option = document.createElement('option');
                    option.value = ds.filename;
                    option.textContent = ds.display_name;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Failed to load saved datasets:', error);
            }
        }

        // Manual Load from dropdowns
        async function loadManualDataset() {
            const saved = document.getElementById('savedDataSelect').value;
            const public = document.getElementById('publicDatasetSelect').value;
            
            if (public) {
                await loadPublicDataset();
            } else if (saved) {
                await loadSavedDataset();
            } else {
                alert('Please select a dataset from the dropdowns first.');
            }
        }



        // Load saved dataset
        async function loadSavedDataset() {
            const filename = document.getElementById('savedDataSelect').value;
            if (!filename) return;

            showLoading('Loading saved dataset...');
            const formData = new FormData();
            formData.append('filename', filename);

            try {
                const response = await axios.post(`${API_BASE}/load-saved`, formData);
                handleDataLoaded(response.data);
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Handle data loaded
        function handleDataLoaded(data) {
            currentFilename = data.filename;
            currentProfile = data.profile;
            classifications = {};

            document.getElementById('currentDataset').textContent = currentFilename;
            document.getElementById('datasetSize').textContent = `${currentProfile.shape.rows.toLocaleString()} rows x ${currentProfile.shape.cols} columns`;
            document.getElementById('datasetInfo').classList.remove('hidden');

            document.getElementById('mainNav').classList.remove('hidden');
            updateStepGuide('analysis');
            showSection('analysis');

            renderInsights();
            renderQuestions();
            renderColumns();
            renderPreview(data.preview);
            populateSelects();
            showTab('summary');

        }


        // Workflow state helper
        function updateStepGuide(activeId) {
            const steps = {
                'upload': { id: 'step1', msg: 'Step 1: Successfully loaded dataset.' },
                'analysis': { id: 'step2', msg: 'Step 2: Look for patterns in your data below.' },
                'modeling': { id: 'step3', msg: 'Step 3: Tell the AI what you want to predict.' }
            };
            
            const baseClass = 'flex items-center gap-2 px-3 py-1.5 rounded-xl border-2 text-xs font-bold uppercase tracking-wider transition-all cursor-pointer hover:opacity-80';

            // Reset all
            ['step1', 'step2', 'step3'].forEach(id => {
                document.getElementById(id).className = baseClass + ' step-todo';
            });

            // Mark previous steps as done
            const order = ['upload', 'analysis', 'modeling'];
            const activeIdx = order.indexOf(activeId);

            for(let i=0; i < activeIdx; i++) {
                document.getElementById(steps[order[i]].id).className = baseClass + ' step-done';
            }

            // Mark current
            document.getElementById(steps[activeId].id).className = baseClass + ' step-active';
            document.querySelector('#guideText span').textContent = steps[activeId].msg;
            document.getElementById('guideText').classList.remove('hidden');
        }

        // Section switching
        function showSection(sectionId) {
            updateStepGuide(sectionId);
            document.querySelectorAll('main > section').forEach(el => el.classList.add('hidden'));
            const targetSection = document.getElementById(sectionId + 'Section');
            if (targetSection) targetSection.classList.remove('hidden');
            
            // Update tab buttons
            document.querySelectorAll('.main-tab-btn').forEach(btn => {
                btn.classList.remove('main-tab-active-data', 'main-tab-active-analysis', 'main-tab-active-modeling', 'text-gray-600', 'bg-gray-100');
                btn.classList.add('text-gray-500', 'hover:bg-gray-50');
                
                if (btn.dataset.section === sectionId) {
                    btn.classList.remove('text-gray-500', 'hover:bg-gray-50');
                    btn.classList.add(`main-tab-active-${sectionId}`);
                }
            });
        }

        function toggleAiSummary() {
            const content = document.getElementById('aiSummaryContent');
            const arrow = document.getElementById('aiSummaryArrow');
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                arrow.textContent = '-';
            } else {
                content.classList.add('hidden');
                arrow.textContent = '+';
            }
        }

        // Render insights
        function renderInsights() {
            const container = document.getElementById('insightsContainer');
            
            container.innerHTML = currentProfile.insights.map(insight => `
                <div class="insight-card p-4 bg-gray-50 rounded-xl border hover:shadow-md transition-all">
                    <div class="flex items-start gap-4">
                        <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl ${
                            insight.type === 'overview' ? 'bg-blue-100 text-blue-600' :
                            insight.type === 'data_quality' ? 'bg-yellow-100 text-yellow-600' :
                            insight.type === 'correlation' ? 'bg-green-100 text-green-600' :
                            insight.type === 'geo_enrichment' ? 'bg-indigo-600 text-white shadow-sm' :
                            'bg-red-100 text-red-600'
                        }">
                            ${insight.type === 'overview' ? '&#128202;' :
                              insight.type === 'data_quality' ? '&#9888;' :
                              insight.type === 'correlation' ? '&#128279;' : 
                              insight.type === 'geo_enrichment' ? '🌍' : '&#128269;'}
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center justify-between gap-2">
                                <h4 class="font-bold text-gray-900">${insight.title}</h4>
                                ${insight.type === 'geo_enrichment' ? `
                                    <button onclick="joinCensus('${insight.hint}', '${insight.column}'); this.remove()" class="px-4 py-1.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 transition-all shadow-sm flex items-center gap-1">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                                        Add Census Data
                                    </button>
                                ` : ''}
                            </div>
                            <p class="text-sm text-gray-600 mt-1">${insight.detail}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        // Render suggested questions
        function renderQuestions() {
            const container = document.getElementById('questionsContainer');
            container.innerHTML = currentProfile.suggested_questions.map((q, i) => `
                <button onclick="executeQuestion(${i})" class="question-btn w-full text-left p-3 border rounded-lg text-sm hover:border-indigo-500">
                    ${q.question}
                </button>
            `).join('');
        }

        // Execute suggested question
        function executeQuestion(index) {
            const question = currentProfile.suggested_questions[index];
            const action = question.action;

            if (action.type === 'pivot') {
                document.getElementById('pivotRows').value = action.rows[0];
                if (action.cols) document.getElementById('pivotCols').value = action.cols[0];
                if (action.values) document.getElementById('pivotValues').value = action.values[0];
                document.getElementById('pivotAgg').value = action.agg || 'sum';
                showTab('pivot');
                createPivot();
            } else if (action.type === 'scatter') {
                document.getElementById('vizType').value = 'scatter';
                updateVizOptions();
                document.getElementById('vizX').value = action.x;
                document.getElementById('vizY').value = action.y;
                showTab('visualize');
                createVisualization();
            } else if (action.type === 'classify') {
                document.getElementById('classifyColumn').value = action.column;
                document.getElementById('classifyMethod').value = action.method;
                document.getElementById('classifyName').value = `${action.column}_${action.method}`;
                showTab('classify');
            }
        }

        // Render columns overview
        function renderColumns() {
            const container = document.getElementById('columnsContainer');
            container.innerHTML = Object.values(currentProfile.columns).map(col => `
                <div class="p-4 border rounded-xl">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-medium text-gray-900">${col.name}</h4>
                        <span class="px-2 py-1 text-xs rounded-full ${
                            col.role === 'measure' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                        }">${col.role}</span>
                    </div>
                    <p class="text-xs text-gray-500 mb-2">${col.type}</p>
                    <div class="text-sm text-gray-600">
                        <p>Unique: ${col.unique} (${col.unique_pct}%)</p>
                        <p>Missing: ${col.missing} (${col.missing_pct}%)</p>
                        ${col.stats ? `<p>Range: ${col.stats.min} - ${col.stats.max}</p>` : ''}
                    </div>
                </div>
            `).join('');
        }

        // Render preview table
        function renderPreview(data) {
            if (!data || data.length === 0) return;

            const columns = Object.keys(data[0]);
            document.getElementById('previewHead').innerHTML = `<tr>${columns.map(c => `<th class="text-left p-2 border-b">${c}</th>`).join('')}</tr>`;
            document.getElementById('previewBody').innerHTML = data.map(row => `
                <tr class="hover:bg-gray-50">${columns.map(c => `<td class="p-2 border-b">${row[c] ?? ''}</td>`).join('')}</tr>
            `).join('');
        }

        // Populate select dropdowns
        function populateSelects() {
            const cols = currentProfile.columns;
            const dimensions = Object.entries(cols).filter(([k, v]) => v.role === 'dimension').map(([k]) => k);
            const measures = Object.entries(cols).filter(([k, v]) => v.role === 'measure').map(([k]) => k);
            const numeric = Object.entries(cols).filter(([k, v]) => v.type === 'continuous' || v.type === 'categorical_numeric').map(([k]) => k);
            const allCols = Object.keys(cols);

            // Classification
            document.getElementById('classifyColumn').innerHTML = numeric.map(c => `<option value="${c}">${c}</option>`).join('');

            // Pivot
            document.getElementById('pivotRows').innerHTML = dimensions.map(c => `<option value="${c}">${c}</option>`).join('');
            document.getElementById('pivotCols').innerHTML = '<option value="">None</option>' + dimensions.map(c => `<option value="${c}">${c}</option>`).join('');
            document.getElementById('pivotValues').innerHTML = measures.map(c => `<option value="${c}">${c}</option>`).join('');
            // Weight column should include all numeric columns (measures + categorical_numeric)
            document.getElementById('pivotWeightCol').innerHTML = numeric.map(c => `<option value="${c}">${c}</option>`).join('');

            // Visualization
            document.getElementById('vizX').innerHTML = allCols.map(c => `<option value="${c}">${c}</option>`).join('');
            document.getElementById('vizY').innerHTML = numeric.map(c => `<option value="${c}">${c}</option>`).join('');
            document.getElementById('vizColor').innerHTML = '<option value="">None</option>' + dimensions.map(c => `<option value="${c}">${c}</option>`).join('');

            // Model target
            document.getElementById('modelTarget').innerHTML = numeric.map(c => `<option value="${c}">${c}</option>`).join('');

            // Census cleanup - handled via insights now
            populateFeatureSelector();
            updateVizOptions();
        }

        // Feature Selector Logic
        function populateFeatureSelector() {
            const list = document.getElementById('allFeaturesList');
            const target = document.getElementById('modelTarget').value;
            const cols = Object.keys(currentProfile.columns);
            
            list.innerHTML = cols
                .filter(c => c !== target)
                .map(c => `
                    <div class="feature-item flex items-center gap-3 px-2 py-1.5 rounded-lg cursor-pointer transition-colors" onclick="toggleFeatureCheckbox('${c}')">
                        <input type="checkbox" id="feat_check_${c}" value="${c}" 
                            ${selectedFeatures.includes(c) ? 'checked' : ''} 
                            class="rounded text-indigo-600 focus:ring-indigo-500"
                            onclick="event.stopPropagation(); handleFeatureToggle('${c}', this.checked)">
                        <label for="feat_check_${c}" class="flex-1 text-sm text-gray-700 cursor-pointer truncate" onclick="event.stopPropagation()">
                            ${c}
                        </label>
                        <span class="text-[10px] text-gray-400 font-mono">${currentProfile.columns[c].type.substring(0, 4)}</span>
                    </div>
                `).join('');

            updateSelectAllState();
        }

        function toggleFeatureCheckbox(feature) {
            const cb = document.getElementById(`feat_check_${feature}`);
            cb.checked = !cb.checked;
            handleFeatureToggle(feature, cb.checked);
        }

        function handleFeatureToggle(feature, checked) {
            if (checked) {
                if (!selectedFeatures.includes(feature)) selectedFeatures.push(feature);
            } else {
                selectedFeatures = selectedFeatures.filter(f => f !== feature);
            }
            updateSelectAllState();
            renderSelectedFeatures();
            
            if (selectedFeatures.length > 0) {
                document.getElementById('trainModelSection').classList.remove('hidden');
            }
        }

        function toggleAllFeatures(checked) {
            const target = document.getElementById('modelTarget').value;
            const cols = Object.keys(currentProfile.columns).filter(c => c !== target);
            
            if (checked) {
                selectedFeatures = [...cols];
            } else {
                selectedFeatures = [];
            }
            
            // Update UI
            document.querySelectorAll('#allFeaturesList input[type="checkbox"]').forEach(cb => {
                cb.checked = checked;
            });
            
            renderSelectedFeatures();
            if (selectedFeatures.length > 0) {
                document.getElementById('trainModelSection').classList.remove('hidden');
            }
        }

        function filterFeatureList(query) {
            const q = query.toLowerCase();
            document.querySelectorAll('.feature-item').forEach(el => {
                const label = el.querySelector('label').textContent.toLowerCase();
                el.style.display = label.includes(q) ? 'flex' : 'none';
            });
        }

        function updateSelectAllState() {
            const target = document.getElementById('modelTarget').value;
            const selectableCols = Object.keys(currentProfile.columns).filter(c => c !== target);
            const selectAll = document.getElementById('selectAllFeatures');
            
            if (selectableCols.length > 0 && selectableCols.every(c => selectedFeatures.includes(c))) {
                selectAll.checked = true;
                selectAll.indeterminate = false;
            } else if (selectedFeatures.length > 0) {
                selectAll.checked = false;
                selectAll.indeterminate = true;
            } else {
                selectAll.checked = false;
                selectAll.indeterminate = false;
            }
        }

        // Tab switching
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('tab-active'));
            document.getElementById(`view-${tabName}`).classList.remove('hidden');
            document.querySelector(`[data-tab="${tabName}"]`).classList.add('tab-active');
        }

        // Create classification
        async function createClassification() {
            const column = document.getElementById('classifyColumn').value;
            const method = document.getElementById('classifyMethod').value;
            const newName = document.getElementById('classifyName').value.trim();

            if (!newName) return alert('Please enter a name for the new column');

            showLoading('Creating classification...');
            try {
                const response = await axios.post(`${API_BASE}/classify`, {
                    filename: currentFilename,
                    column: column,
                    method: method,
                    new_name: newName,
                    params: method === 'kmeans' ? { n_clusters: 4 } : {}
                });

                classifications[newName] = response.data.distribution;
                renderClassifications();
                populateSelectsWithClassifications();
                alert('Classification created!');
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        function filterJoinCols(query) {
            const select = document.getElementById('joinUserColumn');
            if (!select || !currentProfile) return;
            const q = query.toLowerCase();
            const cols = Object.keys(currentProfile.columns);
            
            const currentVal = select.value;
            select.innerHTML = cols
                .filter(c => c.toLowerCase().includes(q))
                .map(c => `<option value="${c}" ${c === currentVal ? 'selected' : ''}>${c}</option>`)
                .join('');
        }

        // Join Census
        async function joinCensus(autoGeo, autoCol, autoFormat) {
            const geography = autoGeo || document.getElementById('joinGeography')?.value;
            const column = autoCol || document.getElementById('joinUserColumn')?.value;
            const format = autoFormat || document.getElementById('joinFormat')?.value || 'name';
            const resultsDiv = document.getElementById('enrichmentResults');

            showLoading('Enriching with Census data...');
            try {
                const response = await axios.post(`${API_BASE}/join-census`, {
                    filename: currentFilename,
                    geography: geography,
                    join_column: column,
                    geography_format: format
                });

                if (response.data.success) {
                    currentProfile = response.data.profile;
                    
                    document.getElementById('datasetSize').textContent = `${currentProfile.shape.rows.toLocaleString()} rows x ${currentProfile.shape.cols} columns`;
                    
                    renderInsights();
                    renderQuestions();
                    renderColumns();
                    renderPreview(response.data.preview);
                    populateSelects();

                    resultsDiv.innerHTML = `
                        <div class="p-4 bg-green-50 border border-green-200 rounded-2xl shadow-sm animate-pulse-once">
                            <div class="flex items-center justify-between gap-2 text-green-800 font-bold mb-3">
                                <div class="flex items-center gap-2">
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                    Enrichment Successful
                                </div>
                                <button onclick="this.parentElement.parentElement.remove()" class="text-green-400 hover:text-green-600">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                                </button>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div class="bg-white/60 p-3 rounded-xl border border-green-100">
                                    <p class="text-[10px] uppercase font-black text-green-600 tracking-wider">Match Accuracy</p>
                                    <p class="text-2xl font-black text-green-900 leading-none mt-1">${response.data.message.match(/(\d+\.?\d*)%/) ? response.data.message.match(/(\d+\.?\d*)%/)[0] : 'N/A'}</p>
                                </div>
                                <div class="bg-white/60 p-3 rounded-xl border border-green-100">
                                    <p class="text-[10px] uppercase font-black text-green-600 tracking-wider">Rows Matched</p>
                                    <p class="text-2xl font-black text-green-900 leading-none mt-1">${response.data.message.match(/Matched (\d+)/) ? response.data.message.match(/Matched (\d+)/)[1] : 'N/A'}</p>
                                </div>
                            </div>
                            <p class="text-xs text-green-700 font-medium mt-3 px-1">${response.data.message.split('. ')[2] || 'New variables added.'}</p>
                            <div class="mt-4 pt-3 border-t border-green-100 flex justify-between items-center">
                                <span class="text-[10px] text-green-500 font-medium italic">Thousands of demographics added.</span>
                                <button onclick="showTab('preview')" class="text-xs bg-green-600 text-white font-bold px-4 py-1.5 rounded-lg hover:bg-green-700 transition-all shadow-md">View Rows</button>
                            </div>
                        </div>
                    `;
                    resultsDiv.classList.remove('hidden');
                    showNotice("Enrichment Complete", "Census variables added.", "success");
                }
            } catch (error) {
                showNotice("Enrichment Failed", (error.response?.data?.detail || error.message), "error");
            } finally {
                hideLoading();
            }
        }


        // Render active classifications
        function renderClassifications() {
            const container = document.getElementById('classificationsContainer');
            if (Object.keys(classifications).length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-sm">No classifications created yet</p>';
                return;
            }

            container.innerHTML = Object.entries(classifications).map(([name, dist]) => `
                <div class="p-3 bg-gray-50 rounded-lg">
                    <h4 class="font-medium text-gray-900">${name}</h4>
                    <div class="mt-2 space-y-1">
                        ${Object.entries(dist).map(([k, v]) => `
                            <div class="flex justify-between text-sm">
                                <span class="text-gray-600">${k}</span>
                                <span class="font-medium">${v}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
        }

        // Add classifications to select dropdowns
        function populateSelectsWithClassifications() {
            const classNames = Object.keys(classifications);

            // Add to pivot dimensions
            const pivotRows = document.getElementById('pivotRows');
            const pivotCols = document.getElementById('pivotCols');
            classNames.forEach(name => {
                if (!pivotRows.querySelector(`option[value="${name}"]`)) {
                    pivotRows.add(new Option(name, name));
                }
                if (!pivotCols.querySelector(`option[value="${name}"]`)) {
                    pivotCols.add(new Option(name, name));
                }
            });

            // Add to viz color
            const vizColor = document.getElementById('vizColor');
            classNames.forEach(name => {
                if (!vizColor.querySelector(`option[value="${name}"]`)) {
                    vizColor.add(new Option(name, name));
                }
            });
        }

        // Toggle weight column visibility based on aggregation selection
        function toggleWeightColumn() {
            const aggfunc = document.getElementById('pivotAgg').value;
            const weightContainer = document.getElementById('pivotWeightContainer');
            if (aggfunc === 'wtd_avg') {
                weightContainer.classList.remove('hidden');
            } else {
                weightContainer.classList.add('hidden');
            }
        }

        // Create pivot table
        async function createPivot() {
            const rows = document.getElementById('pivotRows').value;
            const cols = document.getElementById('pivotCols').value;
            const values = document.getElementById('pivotValues').value;
            const aggfunc = document.getElementById('pivotAgg').value;
            const weightCol = document.getElementById('pivotWeightCol').value;

            // Validate weight column for weighted average
            if (aggfunc === 'wtd_avg' && !weightCol) {
                alert('Please select a weight column for weighted average calculation.');
                return;
            }

            showLoading('Creating pivot table...');
            try {
                const payload = {
                    filename: currentFilename,
                    rows: [rows],
                    cols: cols ? [cols] : null,
                    values: [values],
                    aggfunc: aggfunc
                };
                if (aggfunc === 'wtd_avg') {
                    payload.weight_col = weightCol;
                }

                const response = await axios.post(`${API_BASE}/pivot`, payload);

                renderPivotTable(response.data);
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Render pivot table
        function renderPivotTable(data) {
            const container = document.getElementById('pivotResult');

            if (data.error) {
                container.innerHTML = `<p class="text-red-600">${data.error}</p>`;
                return;
            }

            const cols = data.columns;
            let html = '<table class="pivot-table w-full">';
            html += '<thead><tr>' + cols.map(c => `<th class="text-left">${c}</th>`).join('') + '</tr></thead>';
            html += '<tbody>';

            data.data.forEach(row => {
                const isTotal = row._is_total || (row[cols[0]] === 'TOTAL') || (row[cols[0]] === 'Total');
                html += `<tr class="${isTotal ? 'font-bold bg-gray-100' : ''}">`;
                cols.forEach(c => {
                    let val = row[c];
                    if (typeof val === 'number') val = val.toLocaleString(undefined, { maximumFractionDigits: 2 });
                    html += `<td>${val ?? ''}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table>';
            container.innerHTML = html;
        }

        // Update visualization options based on chart type
        function updateVizOptions() {
            const type = document.getElementById('vizType').value;
            const xContainer = document.getElementById('vizXContainer');
            const yContainer = document.getElementById('vizYContainer');
            const colorContainer = document.getElementById('vizColorContainer');

            if (type === 'correlation') {
                xContainer.classList.add('hidden');
                yContainer.classList.add('hidden');
                colorContainer.classList.add('hidden');
            } else if (type === 'distribution') {
                xContainer.classList.remove('hidden');
                yContainer.classList.add('hidden');
                colorContainer.classList.add('hidden');
            } else if (type === 'scatter') {
                xContainer.classList.remove('hidden');
                yContainer.classList.remove('hidden');
                colorContainer.classList.remove('hidden');
            } else if (type === 'bar') {
                xContainer.classList.remove('hidden');
                yContainer.classList.remove('hidden');
                colorContainer.classList.add('hidden');
            } else if (type === 'cluster') {
                xContainer.classList.remove('hidden');
                yContainer.classList.remove('hidden');
                colorContainer.classList.remove('hidden');
            } else if (type === 'map') {
                xContainer.classList.remove('hidden');
                yContainer.classList.remove('hidden'); // Value to shade by
                colorContainer.classList.remove('hidden'); // Label/Hover info
                document.querySelector('#vizXContainer label').textContent = 'Geography Column (State/ZIP)';
                document.querySelector('#vizYContainer label').textContent = 'Shading Value (Income/etc)';
            }

            if (type !== 'map') {
                document.querySelector('#vizXContainer label').textContent = 'X Axis / Column';
                document.querySelector('#vizYContainer label').textContent = 'Y Axis';
            }
        }

        // Create visualization
        async function createVisualization() {
            const type = document.getElementById('vizType').value;
            const x = document.getElementById('vizX').value;
            const y = document.getElementById('vizY').value;
            const color = document.getElementById('vizColor').value;

            showLoading('Generating chart...');
            try {
                const response = await axios.post(`${API_BASE}/visualize`, {
                    filename: currentFilename,
                    chart_type: type,
                    x: x,
                    y: y,
                    color: color || null,
                    column: x
                });

                if (type === 'map') {
                    renderMap(response.data);
                } else {
                    document.getElementById('vizResult').innerHTML = response.data.image ?
                        `<img src="data:image/png;base64,${response.data.image}" class="max-w-full rounded-lg shadow">` :
                        '<p class="text-gray-500">No chart generated</p>';
                }
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        function renderMap(result) {
            const container = document.getElementById('vizResult');
            container.innerHTML = '<div id="plotlyMap" style="width:100%; height:600px;" class="rounded-xl shadow border bg-white"></div>';
            
            const data = result.map_data;
            const xCol = document.getElementById('vizX').value;
            const yCol = document.getElementById('vizY').value;
            const colorCol = document.getElementById('vizColor').value;

            // Determine if we should do a scatter map (points) or choropleth
            const hasCoords = result.has_coords && data.some(d => d['geo.latitude'] && d['geo.longitude']);
            
            let plotlyData = [];
            let layout = {
                geo: {
                    scope: 'usa',
                    projection: { type: 'albers usa' },
                    showlakes: true,
                    lakecolor: 'rgb(255, 255, 255)'
                },
                margin: { l: 0, r: 0, t: 40, b: 0 },
                title: { text: `US Geographic Distribution: ${yCol || xCol}`, font: { size: 16 } }
            };

            if (hasCoords && (!xCol || xCol.toLowerCase() !== 'state')) {
                // Point Map
                plotlyData.push({
                    type: 'scattergeo',
                    locationmode: 'USA-states',
                    lat: data.map(d => d['geo.latitude']),
                    lon: data.map(d => d['geo.longitude']),
                    text: data.map(d => `${d['name'] || ''}<br>${d[colorCol] || ''}`),
                    mode: 'markers',
                    marker: {
                        size: 5,
                        opacity: 0.8,
                        color: yCol ? data.map(d => d[yCol]) : '#4F46E5',
                        colorscale: 'Viridis',
                        showscale: !!yCol,
                        colorbar: { title: yCol }
                    }
                });
            } else {
                // Choropleth Map (Aggregate by X column if it looks like State)
                const aggData = {};
                data.forEach(d => {
                    const key = d[xCol];
                    if (!key) return;
                    if (!aggData[key]) aggData[key] = { val: 0, count: 0, label: key };
                    aggData[key].val += (parseFloat(d[yCol]) || 0);
                    aggData[key].count += 1;
                });

                const locations = Object.keys(aggData);
                const values = locations.map(loc => aggData[loc].val / (aggData[loc].count || 1));

                plotlyData.push({
                    type: 'choropleth',
                    locationmode: 'USA-states',
                    locations: locations,
                    z: values,
                    text: locations,
                    colorscale: 'Blues',
                    marker: { line: { color: 'rgb(255,255,255)', width: 2 } },
                    colorbar: { title: yCol || 'Count' }
                });
            }

            Plotly.newPlot('plotlyMap', plotlyData, layout, { responsive: true });
        }

        // Analyze features
        async function analyzeFeatures() {
            const target = document.getElementById('modelTarget').value;
            if (!target) return alert('Please select a target variable');

            showLoading('Analyzing feature importance...');
            try {
                const formData = new FormData();
                formData.append('filename', currentFilename);
                formData.append('target', target);

                const response = await axios.post(`${API_BASE}/analyze-features`, formData);
                renderFeatureImportance(response.data);
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Render feature importance
        function renderFeatureImportance(data) {
            // Filter out the target variable from recommended features
            const targetVar = data.target;
            selectedFeatures = data.recommended_features.filter(f => f !== targetVar);

            // Filter out the target from feature rankings as well
            const filteredRankings = data.feature_ranking.filter(f => f.feature !== targetVar);

            // Build encoding type badge
            const encodingBadge = (f) => {
                const colors = {
                    numeric: 'bg-blue-100 text-blue-700',
                    dummy: 'bg-green-100 text-green-700',
                    dummy_top: 'bg-green-100 text-green-700',
                    binary: 'bg-yellow-100 text-yellow-700',
                    group: 'bg-orange-100 text-orange-700'
                };
                const labels = {
                    numeric: 'NUM',
                    dummy: 'CAT',
                    dummy_top: 'CAT',
                    binary: 'BIN',
                    group: 'GRP'
                };
                const cls = colors[f.encoding] || 'bg-gray-100 text-gray-600';
                const lbl = labels[f.encoding] || f.encoding;
                return '<span class="px-1.5 py-0.5 rounded text-[9px] font-bold ' + cls + '">' + lbl + '</span>';
            };

            // Correlation indicator
            const corrIndicator = (f) => {
                if (f.correlation === null || f.correlation === undefined) return '';
                const val = f.correlation;
                const absVal = Math.abs(val);
                let color = 'text-gray-400';
                if (absVal > 0.7) color = val > 0 ? 'text-green-600' : 'text-red-600';
                else if (absVal > 0.4) color = val > 0 ? 'text-green-500' : 'text-red-500';
                return '<span class="text-[10px] ' + color + ' font-mono" title="Pearson correlation with target">r=' + val.toFixed(2) + '</span>';
            };

            // Collinearity warning
            const collinearWarn = (f) => {
                if (!f.is_collinear) return '';
                return '<span class="text-[9px] text-amber-600 font-bold" title="Redundant — highly correlated with another feature">REDUNDANT</span>';
            };

            let html = '<div class="mt-4 space-y-3">';

            // Summary stats
            html += `
                <div class="p-3 bg-indigo-50 rounded-xl border border-indigo-100">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-indigo-900 text-xs uppercase">Analysis Summary</h4>
                        <span class="text-[10px] text-indigo-500">${data.rows_analyzed} rows analyzed</span>
                    </div>
                    <div class="grid grid-cols-3 gap-2 text-center">
                        <div class="p-2 bg-white rounded-lg">
                            <p class="text-lg font-black text-indigo-900">${data.total_features_analyzed}</p>
                            <p class="text-[9px] text-indigo-500 uppercase">Usable</p>
                        </div>
                        <div class="p-2 bg-white rounded-lg">
                            <p class="text-lg font-black text-indigo-900">${data.total_features_dropped}</p>
                            <p class="text-[9px] text-indigo-500 uppercase">Dropped</p>
                        </div>
                        <div class="p-2 bg-white rounded-lg">
                            <p class="text-lg font-black text-indigo-900">${data.recommended_features.length}</p>
                            <p class="text-[9px] text-indigo-500 uppercase">Recommended</p>
                        </div>
                    </div>
                    <p class="text-[9px] text-indigo-400 mt-2 italic">${data.scoring_method}</p>
                </div>
            `;

            // Feature ranking
            html += `
                <div class="p-4 bg-purple-50 rounded-xl border border-purple-100">
                    <h4 class="font-bold text-purple-900 text-xs uppercase mb-3 flex items-center gap-2">
                        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"></path></svg>
                        Feature Ranking (Top 10)
                    </h4>
                    <div class="space-y-2">
                        ${filteredRankings.slice(0, 10).map((f, i) => `
                            <div class="space-y-1 ${f.is_collinear ? 'opacity-50' : ''}">
                                <div class="flex items-center justify-between text-[11px] gap-1">
                                    <div class="flex items-center gap-1.5 min-w-0">
                                        <span class="text-[9px] text-purple-400 font-mono w-3">${i+1}</span>
                                        ${encodingBadge(f)}
                                        <span class="font-semibold text-purple-900 truncate">${f.feature}</span>
                                        ${collinearWarn(f)}
                                    </div>
                                    <div class="flex items-center gap-2 shrink-0">
                                        ${corrIndicator(f)}
                                        <span class="text-purple-600 font-bold">${f.importance_pct}%</span>
                                    </div>
                                </div>
                                <div class="w-full bg-purple-200 rounded-full h-1.5 overflow-hidden">
                                    <div class="bg-purple-600 h-1.5 rounded-full transition-all duration-500" style="width: ${f.importance_pct}%"></div>
                                </div>
                                <p class="text-[9px] text-purple-400 italic pl-4">${f.recommendation}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            // Multicollinearity warnings
            if (data.multicollinearity && data.multicollinearity.length > 0) {
                html += `
                    <div class="p-3 bg-amber-50 rounded-xl border border-amber-200">
                        <h4 class="font-bold text-amber-800 text-xs uppercase mb-2 flex items-center gap-1">
                            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
                            Multicollinearity Detected
                        </h4>
                        <div class="space-y-1">
                            ${data.multicollinearity.map(m => `
                                <div class="text-[10px] text-amber-700">
                                    <span class="font-semibold">${m.feature_a}</span> &harr; <span class="font-semibold">${m.feature_b}</span>
                                    <span class="text-amber-500">(r=${m.correlation})</span>
                                    &mdash; ${m.recommendation}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            // Dropped features
            if (data.dropped_features && data.dropped_features.length > 0) {
                html += `
                    <div class="p-3 bg-gray-50 rounded-xl border border-gray-200">
                        <h4 class="font-bold text-gray-600 text-xs uppercase mb-2">Dropped Features (${data.dropped_features.length})</h4>
                        <div class="space-y-0.5">
                            ${data.dropped_features.map(d => `
                                <div class="text-[10px] text-gray-500">
                                    <span class="font-semibold">${d.feature}</span> &mdash; ${d.reason}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            html += '</div>';

            document.getElementById('featureImportanceResult').innerHTML = html;

            populateFeatureSelector();
            document.getElementById('trainModelSection').classList.remove('hidden');
            renderSelectedFeatures();
        }

        function toggleFeature(feature) {
            if (selectedFeatures.includes(feature)) {
                selectedFeatures = selectedFeatures.filter(f => f !== feature);
            } else {
                selectedFeatures.push(feature);
            }
            renderSelectedFeatures();
        }

        function renderSelectedFeatures() {
            document.getElementById('selectedFeatures').innerHTML = selectedFeatures.map(f => `
                <span class="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-sm">${f}</span>
            `).join('');
        }

        // Train model
        async function trainModel() {
            if (selectedFeatures.length === 0) return alert('Please select at least one feature');

            const target = document.getElementById('modelTarget').value;
            const modelType = document.getElementById('modelType').value;

            showLoading('Training model...');
            try {
                const formData = new FormData();
                formData.append('filename', currentFilename);
                formData.append('target', target);
                formData.append('features', selectedFeatures.join(','));
                formData.append('model_type', modelType);

                const response = await axios.post(`${API_BASE}/train-model`, formData);
                renderModelResults(response.data);
                
                // Fetch AI Executive Summary
                fetchModelSummary();
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Render model results
        function renderModelResults(data) {
            modelFormFields = data.form_fields;
            const r2 = data.stats.test_r2;
            
            let quality = "Low";
            let color = "red";
            let icon = "⚠️";
            
            if (r2 > 0.85) {
                quality = "Excellent";
                color = "green";
                icon = "✨";
            } else if (r2 > 0.5) {
                quality = "Good";
                color = "blue";
                icon = "✅";
            }

            document.getElementById('modelResults').innerHTML = `
                <div class="p-5 bg-${color}-50 border border-${color}-200 rounded-2xl shadow-sm">
                    <div class="flex items-start justify-between mb-4">
                        <div>
                            <h4 class="font-bold text-${color}-900 text-lg flex items-center gap-2">
                                <span>${icon}</span>
                                Prediction Quality: ${quality}
                            </h4>
                            <p class="text-sm text-${color}-700 mt-1">
                                ${quality === 'Excellent' ? 'Highly reliable for making business decisions.' : 
                                  quality === 'Good' ? 'Good for identifying general trends and patterns.' : 
                                  'This model is struggling to find clear patterns. Use with caution.'}
                            </p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-3 bg-white/50 rounded-xl border border-${color}-100">
                            <p class="text-[10px] uppercase font-bold text-${color}-500 tracking-wider">Overall Accuracy</p>
                            <p class="text-2xl font-black text-${color}-900">${(r2 * 100).toFixed(1)}%</p>
                        </div>
                        <div class="p-3 bg-white/50 rounded-xl border border-${color}-100">
                            <p class="text-[10px] uppercase font-bold text-${color}-500 tracking-wider">Margin of Error</p>
                            <p class="text-2xl font-black text-${color}-900">±${data.stats.test_mae}</p>
                        </div>
                    </div>
                    
                    <div class="mt-4 pt-3 border-t border-${color}-100 text-[10px] text-${color}-500 flex justify-between">
                        <span>Model: ${data.stats.model_type}</span>
                        <span>Sample Size: ${data.stats.test_samples} records</span>
                    </div>
                </div>
            `;

            // Render prediction form
            document.getElementById('predictionInputs').innerHTML = modelFormFields.map(field => `
                <div>
                    <label class="block text-sm text-gray-600 mb-1">${field.label}</label>
                    ${field.input_type === 'number' ? `
                        <input type="number" id="pred_${field.name}" value="${field.default}"
                            min="${field.min}" max="${field.max}" step="any"
                            class="w-full px-3 py-2 border rounded-lg">
                        <p class="text-xs text-gray-400 mt-1">${field.tooltip || ''}</p>
                    ` : `
                        <select id="pred_${field.name}" class="w-full px-3 py-2 border rounded-lg">
                            ${field.options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
                        </select>
                    `}
                </div>
            `).join('');

            document.getElementById('predictionForm').classList.remove('hidden');
        }

        // Fetch AI Executive Summary
        async function fetchModelSummary() {
            const container = document.getElementById('aiSummaryContainer');
            const summaryDiv = document.getElementById('aiSummary');
            
            container.classList.remove('hidden');
            summaryDiv.innerHTML = '<div class="flex items-center gap-2"><div class="loader w-4 h-4 border-2"></div> Thinking...</div>';
            
            try {
                const formData = new FormData();
                formData.append('filename', currentFilename);
                
                const response = await axios.post(`${API_BASE}/model-summary`, formData);
                
                if (response.data && response.data.summary) {
                    const text = response.data.summary;
                    summaryDiv.innerHTML = text.split('\\n').filter(p => p.trim()).map(p => `<p class="mb-2">${p}</p>`).join('');
                } else {
                    summaryDiv.innerHTML = '<span class="text-gray-500 italic">Analysis complete, but no summary text was returned.</span>';
                }
            } catch (error) {
                console.error('Summary error:', error);
                summaryDiv.innerHTML = `<span class="text-red-500 italic text-xs">AI summary unavailable: ${error.message}</span>`;
            }
        }

        // Make prediction
        async function makePrediction() {
            const inputData = {};
            modelFormFields.forEach(field => {
                const el = document.getElementById(`pred_${field.name}`);
                inputData[field.name] = field.input_type === 'number' ? parseFloat(el.value) : el.value;
            });

            showLoading('Making prediction...');
            try {
                const formData = new FormData();
                formData.append('filename', currentFilename);
                formData.append('input_data', JSON.stringify(inputData));

                const response = await axios.post(`${API_BASE}/predict`, formData);

                document.getElementById('predictionResult').innerHTML = `
                    <div class="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg text-center">
                        <p class="text-sm text-gray-600">Predicted Value</p>
                        <p class="text-3xl font-bold text-indigo-600">${response.data.prediction}</p>
                        <p class="text-xs text-gray-500 mt-1">Range: ${response.data.lower_bound} - ${response.data.upper_bound}</p>
                    </div>
                `;
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Export data
        async function exportData(format) {
            showLoading('Exporting...');
            try {
                const response = await axios.get(`${API_BASE}/export/${currentFilename}?format=${format}`);

                const blob = new Blob([response.data.data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = response.data.filename;
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('Error: ' + (error.response?.data?.detail || error.message));
            } finally {
                hideLoading();
            }
        }

        // Reset analysis
        function resetAnalysis() {
            currentFilename = null;
            currentProfile = null;
            classifications = {};

            document.getElementById('datasetInfo').classList.add('hidden');
            document.getElementById('mainNav').classList.add('hidden');
            showSection('upload');

            document.getElementById('publicDatasetSelect').value = '';
            document.getElementById('urlInput').value = '';
            document.getElementById('fileInput').value = '';
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            // Check for mobile user agents as well as screen width
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            if (isMobile) {
                document.getElementById('mobileWarning').style.display = 'flex';
            }

            updateVizOptions();
            populateSavedDatasets();
            showSection('upload');
        });
    </script>
</body>
</html>
"""

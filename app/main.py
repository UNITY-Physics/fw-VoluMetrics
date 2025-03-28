from fpdf import FPDF
from datetime import datetime
from PyPDF2 import PdfMerger
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame,SimpleDocTemplate, Table, TableStyle, PageBreak, Spacer,  PageTemplate, Frame
from reportlab.lib.utils import ImageReader
import statsmodels.api as sm

import textwrap
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import os
import itertools
import warnings

from utils.format import beautify_report, scale_image, simplify_label, generate_on_page

warnings.simplefilter('ignore', np.RankWarning)

output_dir ='/flywheel/v0/output/'
workdir = '/flywheel/v0/work/'


# Define the bins and labels
# These have been setup with finer granularity early on due to rapid growth and then coarser granularity later
global bins 
global labels
global range_mapping
global label_mapping
global bins_mapping

bins = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 21, 24, 30, 36, 48, 60, 72, 84, 96, 108, 120, 144, 168, 192, 216, 252, 300]
labels = ['0-1 month', '1-2 months', '2-3 months', '3-4 months', '4-5 months', '5-6 months',
        '6-8 months', '8-10 months', '10-12 months', '12-15 months', '15-18 months', 
        '18-21 months', '21-24 months', '24-30 months', '30-36 months','3-4 years', 
        '4-5 years', '5-6 years', '6-7 years', '7-8 years', '8-9 years', '9-10 years', 
        '10-12 years', '12-14 years', '14-16 years', '16-18 years', '18-21 years', '21-25 years']


range_mapping =  {"Infants (0-12 months)": (0, 12),
"1st 1000 Days (0-32 months)": (0,32),
"Toddlers (1-3 years)": (12, 36),
"Preschool (3-6 years)": (36, 72),
"School-age Children (6-12 years)": (72, 144),
"Adolescents (12-18 years)": (144, 216),
"Young Adults (18-34 years)": (216, 408),
"Adults (35-89 years)": (420, 1068),  
"All Ages (0-100 years)": (0, 1200) 
}

label_mapping = {
"Infants (0-12 months)": ['0-1 month', '1-2 months', '2-3 months', '3-4 months', '4-5 months', '5-6 months','6-8 months', '8-10 months', '10-12 months'],
"1st 1000 Days (0-32 months)" : ['0-1 month', '1-2 months', '2-3 months', '3-4 months', '4-5 months', '5-6 months','6-8 months', '8-10 months', '10-12 months', '12-15 months', '15-18 months', '18-21 months', '21-24 months', '24-30 months', '30-36 months'],
"Toddlers (1-3 years)": ['12-15 months', '15-18 months', '18-21 months', '21-24 months', '24-30 months', '30-36 months'],
"Preschool (3-6 years)": ['3-4 years','4-5 years', '5-6 years'],
"School-age Children (6-12 years)": ['6-7 years', '7-8 years', '8-9 years', '9-10 years', '10-12 years'],
"Adolescents (12-18 years)": ['12-14 years', '14-16 years', '16-18 years'],
"Young Adults (18-34 years)": ['18-21 years', '21-24 years','25-29 years', '30-34 years'],
"Adults (35-89 years)":['35-39 years', '40-44 years','45-49 years','50-54 years','55-59 years','60-64 years','65-69 years','70-74 years','75-79 years','80-84 years','85-89 years'],
"All Ages (0-100 years)":["0-12 months", "12-36 months", "3-6 years", "6-10 years", "10-12 years", "12-18 years", "18-25 years", "25-34 years", "34-50 years", "50-60 years", "60-70 years", "70-80 years", "80-90 years", "90-100 years"]

}

bins_mapping = {
"Infants (0-12 months)": [0, 1, 2, 3, 4, 5, 6, 8, 10, 12],
"1st 1000 Days (0-32 months)": [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 21, 24, 30, 36],
"Toddlers (1-3 years)": [12, 15, 18, 21, 24, 30, 36],
"Preschool (3-6 years)": [36, 48, 60, 72],
"School-age Children (6-12 years)": [72, 84, 96, 108, 120, 144],
"Adolescents (12-18 years)": [144, 168, 192, 216],
"Young Adults (18-34 years)": [216, 240, 264, 288, 312, 336],
"Adults (35-89 years)": [420, 444, 468, 492, 516, 540, 564, 588, 612, 636, 660, 684, 708, 732, 756, 780, 804, 828, 852, 876, 900, 924, 948, 972, 996, 1020, 1044, 1068],
"All Ages (0-100 years)": [0, 12, 36, 72, 120, 144, 216, 300, 408, 600, 720, 840, 960, 1080, 1200]  # Covers all from 0 months to 100 years
}

def get_ycoordinate(plot_path):

    page_width, page_height = A4
    image = ImageReader(plot_path)
    # Get the width and height of the image
    img_width, img_height = image.getSize()
    # Ensure the image fits within the page width
    if img_width > page_width - 200:  # Subtract margins
        scale_factor = (page_width - 200) / img_width
        img_width = img_width * scale_factor
        img_height = img_height * scale_factor

    # Set initial y-coordinate for the first image
    y_coordinate = page_height - img_height - 140  # Leave some space from the top

    next_y_coordinate = y_coordinate - img_height - 20 

    return next_y_coordinate

# 1. Generate Cover Page
def create_cover_page(user, input_labels, age_range, age_min, age_max, threshold, project,output_dir):

    global bins 
    global labels
    global range_mapping
    global label_mapping
    global bins_mapping

    if age_range != "":

        age_min = range_mapping[age_range][0] 
        age_max = range_mapping[age_range][1] 
        labels = label_mapping[age_range]
        bins = bins_mapping[age_range]

    print("AGE MIN: ", age_min, 'AGE MAX', age_max,"age range", age_range, bins)

    filename = 'cover_page'
    cover = f"{output_dir}{filename}.pdf"

    # Ensure the directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a new PDF canvas
    doc = SimpleDocTemplate(os.path.join(output_dir, f"{filename}.pdf"), pagesize=A4)
    page_width, page_height = A4

    # Styles
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontSize = 12  # override fontsize because default stylesheet is too small
    styleN.leading = 15
    # Add left and right indentation
    styleN.leftIndent = 20  # Set left indentation
    styleN.rightIndent = 20  # Set right indentation

    # Create a custom style
    custom_style = ParagraphStyle(name="CustomStyle", parent=styleN,
                              fontSize=12,
                              leading=15,
                              alignment=0,  # Centered
                              leftIndent=20,
                              rightIndent=20,
                              spaceBefore=10,
                              spaceAfter=10)


    # Main text (equivalent to `multi_cell` in FPDF)
    text = ("This report provides a detailed summary of the input-derived data. "
            "The data are analyzed by age group and sex. Analyses include the calculation of brain volume z-scores for different age groups, summary descriptive statistics of the total intracranial volume (TICV), and the age distribution in the cohort. of brain volume z-scores for different age groups."
            f"List of outliers has been generated based on z-scores outside of ±{threshold} SD. "
            "Custom options such as age filtering and polynomial fitting have been applied to the data."
            f"<b><br/><br/>Project Description:</b> {project.description}")
    
    custom_options_text = ( f"<br/><br/>Custom Options used:<br />"
                            f"1. Age Range: {age_min}-{age_max} months<br/>"
                            f"2. Outlier Threshold: ±{threshold} SD<br/>"
                            "3. Polynomial Fit: Degree 3 (Cubic)<br/>"
                            "4. Confidence Interval: 95% <br/><br/>"
                            f"<i>Input file used: {input_labels['volumetric']}</i>")
    
    stylesheet = getSampleStyleSheet()
    stylesheet.add(ParagraphStyle(name='Paragraph', spaceAfter=20))
    elements = []
    elements.append(Paragraph(text + custom_options_text, stylesheet['Paragraph']))

    # Define a frame for the content to flow into
    page_width, page_height = A4
    margin = 40
    frame = Frame(margin, -60, page_width - 2 * margin, page_height - 2 * margin, id='normal')

    # Define the PageTemplate with the custom "beautify_report" function for adding logo/border
    template = PageTemplate(id='CustomPage', frames=[frame], onPage=generate_on_page(user,project.label,age_min,age_max,threshold,input_labels))

    # Build the document
    doc.addPageTemplates([template])
    doc.build(elements)
    print("Cover page has been generated.")

    return cover, age_min, age_max


# 2. Parse the volumetric CSV File
def parse_csv(filepath, project_label, age_range, age_min, age_max, threshold):

    """Parse the input CSV file.

    Returns:
        filtered_df (pd.DataFrame): Filtered DataFrame based on age range.
        n (int): Number of observations in the filtered data.
        n_projects (int): Number of unique projects in the filtered data.
        project_labels (list): Unique project labels in the filtered data.
        n_sessions (int): Number of unique sessions in the original data.
        n_clean_sessions (int): Number of unique sessions in the clean data after removing outliers.
        outlier_n (int): Number of participants flagged as outliers based on
    """

    global bins 
    global labels
    global range_mapping
    global label_mapping
    global bins_mapping
        
    # Example DataFrame with ages in months
    df = pd.read_csv(filepath) #
    n_sessions = df['session'].nunique()  # Number of unique sessions
    print("Number of unique sessions: ", n_sessions)
   

    if age_range != "":
        age_min = range_mapping[age_range][0] 
        age_max = range_mapping[age_range][1] 
        labels = label_mapping[age_range]
        bins = bins_mapping[age_range]
    
    # Bin the ages
    #print(bins,labels)

    # A simple heuristic: if the maximum value is above a threshold, consider it as days
    threshold = 100  # adjust based on your dataset context
    print("Max age: ", df['age'].max())
    if df['age'].max() > threshold:
        print("The age values are likely in days.")
        # Rename the 'age' column to 'age_in_days'
        df.rename(columns={'age': 'age_in_days'}, inplace=True)
        df['age_in_months'] = df['age_in_days'] / 30.44
    else:
        print("The age values are likely in months.")
        df.rename(columns={'age': 'age_in_months'}, inplace=True)
        

    df['age_group'] = pd.cut(df['age_in_months'], bins=bins, labels=labels, right=False)

    print("NA Sex:", df.sex.isna().sum())
    print("NA Age:", df.age_in_months.isna().sum())
    print('NA TICV:', df['total intracranial'].isna().sum())

    # Group by sex and age group
    grouped = df.groupby(['sex', 'age_group'])


    # Calculate mean and std for each group
    df['mean_total_intracranial'] = grouped['total intracranial'].transform('mean')
    df['std_total_intracranial'] = grouped['total intracranial'].transform('std')

    # Calculate z-scores
    df['z_score'] = (df['total intracranial'] - df['mean_total_intracranial']) / df['std_total_intracranial']
    # Check if 'project_label' exists, if not, assign a default value
    if 'project_label' not in df.columns:
        df['project_label'] = project_label  # Or any default value like None

    
    # Calculate other volumes
    df['total cerebral white matter'] = df['left cerebral white matter'] + df['right cerebral white matter']
    df['total cerebral cortex'] = df['left cerebral cortex'] + df['right cerebral cortex']
    df['hippocampus'] = df['left hippocampus'] + df['right hippocampus']
    df['thalamus'] = df['left thalamus'] + df['right thalamus']
    df['amygdala'] = df['left amygdala'] + df['right amygdala']
    df['putamen'] = df['left putamen'] + df['right putamen']
    df['caudate'] = df['left caudate'] + df['right caudate']


    used_age_groups = [age for age in labels if age in df['age_group'].unique()]
    # Calculate the count of participants per age group``
    age_group_counts = df['age_group'].value_counts().sort_index()

    # Ensure that 'age_group' is treated as a categorical variable with the correct order (only for used categories)
    df['age_group'] = pd.Categorical(df['age_group'], categories=used_age_groups, ordered=True)
    
    # Define the list of columns you want to retain
    
    volumetric_cols = ['total intracranial', 'z_score', 'total cerebral white matter', 'total cerebral cortex', 'hippocampus', 
                   'thalamus', 'amygdala', 'putamen', 'caudate']
    columns_to_keep = ['project_label', 'subject',	'session',	'age_in_months', 'sex',	'acquisition'] + volumetric_cols
    
    for col in volumetric_cols:

        # Calculate mean and std for each group
        df[f'mean_{col}'] = grouped[col].transform('mean')
        df[f'std_{col}'] = grouped[col].transform('std')

        # Calculate z-scores
        df[f'z_score_{col}'] = (df[col] - df[f'mean_{col}']) / df[f'std_{col}']

        
    # Filter the DataFrame for subjects with z-scores outside of ±1.5 SD and retain only the specified columns
    outliers_df = df[(df['z_score'] < - threshold) | (df['z_score'] > threshold)][columns_to_keep]
    df["is_outlier"] = (df['z_score'] < -threshold) | (df['z_score'] > threshold)

    
    # Save the filtered DataFrame to a CSV file
    outliers_df.to_csv(os.path.join(output_dir,'outliers_list.csv'), index=False)
    outlier_n = len(outliers_df)

    # Step 3: Create a clean DataFrame by excluding the outliers
    clean_df = df[~df.index.isin(outliers_df.index)]

    n_clean_sessions = clean_df['session'].nunique()  # Number of unique sessions in the clean data

    # Optional: Save the clean DataFrame to a CSV file
    clean_df.to_csv(os.path.join(workdir,'clean_data.csv'), index=False)


    # Set limit for the age range to be included in the analysis
    upper_age_limit = age_max
    lower_age_limit = age_min  

    # Filter the data to include only observations up to the requested limit
    filtered_df = clean_df[(clean_df['age_in_months'] <= upper_age_limit) & (clean_df['age_in_months'] >= lower_age_limit)]

    n = len(filtered_df)  # Number of observations in the filtered data
    n_projects = filtered_df['project_label'].nunique()  # Number of unique projects in the filtered data
    project_labels = filtered_df['project_label'].unique()  # Unique project labels in the filtered data

    # --- Generate a summary report with plots and tables --- #

    # Calculate the count (n) for each age group
    age_group_counts = clean_df['age_group'].value_counts().sort_index()
    # Filter out age groups with a count of 0
    age_group_counts = age_group_counts[age_group_counts > 0]


    # Group by sex and age group and calculate the necessary statistics
    summary_table = clean_df.groupby(['age_group', 'sex']).agg({
        'subject': 'nunique',  # Count the number of unique participants
        'session': 'nunique',  # Count the number of unique sessions
        'total intracranial': ['mean', 'std']  # Mean and std of brain volume
    }).reset_index()

    # Remove rows where the mean of 'total intracranial' is NaN
    summary_table = summary_table.dropna(subset=[('total intracranial', 'mean')])
    # Pivot the table to have Sex as columns and Age Group as a single row index
    summary_table = summary_table.pivot(index='age_group', columns='sex')

  
    # Flatten the multi-level columns
    summary_table.columns = ['_'.join(col).strip() for col in summary_table.columns.values]

    # Reset index to make 'age_group' a column
    summary_table.reset_index(inplace=True)

    # Renaming columns for better readability
    summary_table.columns = [
        'Age Group', 
        'n sub (M)', 'n sub (F)', 
        'n ses (M)', 'n ses (F)',  
        'Mean TICV (M)', 'Mean TICV (F)', 
        'Std TICV (M)', 'Std TICV (F)'
    ]

    # Round the numerical columns to 2 decimal places
    summary_table = summary_table.round(2)
    summary_table.to_csv(os.path.join(workdir,'summary_table.csv'),index=False)


    #### Plotting outliers #####
    #outliers_df
    sns.kdeplot(df.loc[df['is_outlier'] == False, 'total intracranial'], label='Non-Outliers')
    sns.kdeplot(df.loc[df['is_outlier'] == True, 'total intracranial'], label='Outliers', color='red')
    plt.title('Distribution of TICV of outliers vs non-outliers')
    plt.legend()
    plt.savefig(os.path.join(workdir, "outlier_icv_plot.png"))

    # Count missing values
    missing_counts = df[["age_in_months", "sex"]].isna().sum()
    
    # Plot
    plt.figure(figsize=(6, 4))
    missing_counts.plot(kind="bar", color="#D96B6B", linewidth=1)

    # Styling
    plt.ylabel("Number of observations")
    plt.title("Missing metadata")
    plt.xticks(rotation=0)  # Keep labels horizontal

    # Add explanation text below the plot
    plt.figtext(0.13, 0.28, 
                "Missing sex and age information affects the usability of this report.\n"
                "Please ensure the metadata is available in your project.\nn"
               )  # Added padding for better spacing


    plt.savefig(os.path.join(output_dir, "missing_metadata.png"))


    return df, summary_table, filtered_df, n, n_projects, n_sessions, n_clean_sessions, outlier_n, project_labels, labels


# 3. Generate the Data Report
def create_data_report(df, summary_table, filtered_df, n, n_projects, n_sessions, n_clean_sessions, outlier_n, project_labels, labels, age_range, age_min, age_max, threshold,output_dir,api_key):

    """Generate a data report with multiple plots and a summary table in a PDF format.

    Returns: report filename
        
    """

    filename = "data_report"
    report = f'{workdir}{filename}.pdf'
    pdf = canvas.Canvas((f'{workdir}{filename}.pdf') )
    a4_fig_size = (8.27, 11.69)  # A4 size
    # Define the page size
    page_width, page_height = A4
    max_width = 300  # Maximum width in points
    max_height = page_width / 3  # Maximum height in points
    
    # --- Plot 1: Boxplot of all Z-Scores by Age Group with Sample Sizes --- #

    # Drop observations where 'age_group' is NaN
    df = df.dropna(subset=['age_group'])

    used_age_groups = [age for age in labels if age in df['age_group'].unique()]

    # Ensure that 'age_group' is treated as a categorical variable with the correct order (only for used categories)
    df['age_group'] = pd.Categorical(df['age_group'], categories=used_age_groups, ordered=True)

    # Calculate the count of participants per age group
    age_group_counts = df['age_group'].value_counts().sort_index()

    # Create new labels with counts
    age_group_labels = [f"{label}\n(n={age_group_counts[label]})" for label in used_age_groups]


    # Dynamically adjust font size based on the number of labeé&ls
    n_labels = len(used_age_groups)
    font_size = max(6, 8 - n_labels // 3)  # Scale the font size down as the number of labels increases. [Not used]

    # Create figure with full A4 size using plt.figure() (not plt.subplots)
    fig = plt.figure(figsize=(10,12))

    # Define the position and size of the smaller figure within the A4 page
    # The numbers in add_axes([left, bottom, width, height]) are relative to the figure size, between 0 and 1
    ax = fig.add_axes([0.125, 0.5, 0.8, 0.4])  # Left, bottom, width, height (adjust these as needed)

    # Set the plot size and create the boxplot
    # fig, ax = plt.subplots(figsize=a4_fig_size)
    sns.boxplot(x='age_group', y='z_score', data=df, ax=ax, order=used_age_groups, palette='Set2', legend=False, hue='age_group')
    ax.set_title('Z-Scores by Age Group')
    ax.set_xlabel('Age Group')
    ax.set_ylabel('Z-Score')

    # Adjust layout so that the plot takes only half of the A4 page (using height ratios)
    #plt.subplots_adjust(top=0.9, bottom=0.6)  # Adjust 'bottom' to fit the lower half, 'top' to adjust upper limit
    
    # Set x-axis tick labels to show the age group labels in the correct order
    ax.set_xticklabels(age_group_labels, rotation=45)
    plt.setp(ax.get_xticklabels(), rotation=45, fontsize=10)  # Shift labels slightly to the left
    ax.grid(True)

    # Add explanation text below the plot
    plt.figtext(0.13, 0.28, 
                "This boxplot displays the distribution of z-scores by age group.\n"
                "Each box represents the interquartile range, with whiskers extending\n"
                f"to show the range within {threshold} times the IQR.\n"
                f"Total number of unique sessions = {n_sessions}\n"
                f"Number of sessions after removing outliers = {n_clean_sessions}\n"
                f"{outlier_n} participant(s) fell outside the {threshold} IQR range and are flagged for further review.",
                wrap=True, horizontalalignment='left', fontsize=11,
                bbox={'facecolor': 'lightgray', 'alpha': 0.5, 'pad': 11})  # Added padding for better spacing

    # Adjust layout to ensure no overlap
    plt.subplots_adjust(top=0.85, bottom=0.4)  # Adjust to fit title and text properly
    # Save the plot only
    plot_path = os.path.join(workdir, "zscores_agegroup_plot.png")
    #plt.tight_layout()
    plt.savefig(plot_path)

    pdf.drawImage(plot_path, 70, -120, width= 500, preserveAspectRatio=True)   # Position plot higher on the page
    plt.close()

    # Calculate y-coordinate for the next image (descriptive stats)  
    next_y_coordinate = get_ycoordinate(plot_path)
    # --- Plot 2: Summary Table of all Participants --- # 
    summary_table = pd.read_csv(os.path.join(workdir,'summary_table.csv'))    
    summary_table.fillna(0,inplace=True)

    # Create figure

    # Apply formatting rules
    for col in summary_table.columns:
        if col.startswith("n "):
            summary_table[col] = summary_table[col].apply(lambda x: int(round(x)))
    i = 0
    for sex in ["M","F"]:
        sub_ses = summary_table[f"n sub ({sex})"].astype(str) + " / " + summary_table[f"n ses ({sex})"].astype(str)
        summary_table.insert(i+1, f"n ({sex}) \n(subs/ses)", sub_ses)

    # Drop the original individual columns
    summary_table = summary_table.drop(columns=["n sub (F)", "n ses (F)", "n sub (M)", "n ses (M)"])

    # Create figure
    fig = plt.figure(figsize=(11.7, 8.3))  # A4 size in inches (approx.)
    ax = fig.add_axes([0.05, 0.3, 0.9, 0.6])  # Adjust the table position

    # Add Title
    # plt.text(0.5, 0.95, 'Summary Descriptive Statistics', fontsize=14, ha='center', transform=fig.transFigure)

    # Turn off axes
    ax.axis('tight')
    ax.axis('off')

    # Create table
    table = ax.table(
        cellText=summary_table.values,
        colLabels=summary_table.columns,
        cellLoc='center',
        loc='center'
    )

    # Customize table appearance
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(0.9, 2)  # Adjust scaling (wider and taller)
    ax.set_title('Summary Descriptive Statistics',fontdict={'fontsize':12})
    # Add explanation text below the table


    # plt.figtext(0.22, 0.84,
    #             "This table summarizes the descriptive statistics for the participants,\n"
    #             "including the number of participants and sessions by sex and age group.",
    #             wrap=True, horizontalalignment='left', fontsize=12,
    #             bbox={'facecolor': 'lightgray', 'alpha': 0.5, 'pad': 10})  # Added padding for better spacing


    # Add some styling
    for key, cell in table.get_celld().items():
        if key[0] == 0:  # Header row
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#40466e')  # Dark header background
        else:
            cell.set_facecolor('#f0f0f0')  # Light gray background for data rows

    # Adjust layout to ensure no overlap
    plt.subplots_adjust(top=0.85, bottom=0.8)  # Adjust to fit title and text properly
    plot_path = os.path.join(workdir, "descriptive_stats.png")
    plt.tight_layout()
    plt.savefig(plot_path,bbox_inches='tight')

    image = ImageReader(plot_path)
    # Get the width and height of the image
    img_width, img_height = image.getSize()

    #pdf.savefig()  # Save the table to the PDF
    plt.close()
    pdf.drawImage(plot_path, 75, next_y_coordinate+150, width= 500, preserveAspectRatio=True)   # Position plot higher on the page
    
    pdf = beautify_report(pdf,False,True)
    pdf.showPage()

    next_y_coordinate = get_ycoordinate(plot_path)

    # --- Plot 3: Histogram of Z-Scores --- #
    
    # Create figure with full A4 size using plt.figure() (not plt.subplots)
    fig = plt.figure(figsize=a4_fig_size)

    # Define the position and size of the smaller figure within the A4 page
    # The numbers in add_axes([left, bottom, width, height]) are relative to the figure size, between 0 and 1
    ax = fig.add_axes([0.125, 0.5, 0.8, 0.4])  # Left, bottom, width, height (adjust these as needed)

    # fig, ax = plt.subplots(figsize=a4_fig_size)
    sns.histplot(filtered_df['age_in_months'], bins=20, kde=True, ax=ax)
    ax.set_title('Distribution of Age in Months')
    ax.set_xlabel('Age (months)')
    ax.set_ylabel('Frequency')
    ax.grid(True)
    
    # Add explanation text below the plot
    plt.figtext(0.15, 0.35, "This plot shows the distribution of participant ages in months.\n"
                        "The KDE curve provides a smoothed estimate of the age distribution.\n"
                        f"Plot limits set to {age_min}-{age_max} months, n = {n}.\n"
                        f"Included projects = {', '.join(project_labels)}",
                wrap=True, horizontalalignment='left', fontsize=12,
                bbox={'facecolor': 'lightgray', 'alpha': 0.5, 'pad': 15})  # Added padding for better spacing

    # Adjust layout to ensure no overlap
    plt.subplots_adjust(top=0.85, bottom=0.2)  # Adjust to fit title and text properly
    plot_path = os.path.join(workdir, "agedist_plot.png")
    

    #plt.tight_layout()
    plt.savefig(plot_path)
    #pdf.savefig()  # Save plot and text to the PDF
    plt.close()

    pdf.drawImage(plot_path, 75, -50, width= 400, preserveAspectRatio=True)   # Position plot higher on the page

    plt.close()

    # Calculate y-coordinate for the next image (scatterplot)
    next_y_coordinate = get_ycoordinate(plot_path)


    # --- Plot 4: Polynomial fit with degree 3 (cubic) using sns.regplot --- #
    # Create figure with full A4 size using plt.figure() (not plt.subplots)
    fig = plt.figure(figsize=a4_fig_size)
    ax = fig.add_axes([0.125, 0.5, 0.8, 0.4])  # Left, bottom, width, height (adjust these as needed)

    # fig, ax = plt.subplots(figsize=a4_fig_size)
    sns.scatterplot(x='age_in_months', y='total intracranial', hue='sex', data=filtered_df, ax=ax)
    for sex in filtered_df['sex'].unique():
        sex_df = filtered_df[filtered_df['sex'] == sex]

        sns.regplot(
            x='age_in_months', 
            y='total intracranial', 
            data=sex_df, 
            order=3,  # Polynomial degree (3 for cubic)
            scatter=False, 
            ci=95,  # Confidence interval
            ax=ax
        )
    ax.set_title('Brain Volume vs. Age, Split by Sex (Polynomial Fit with CI)')
    ax.set_xlabel('Age (months)')
    ax.set_ylabel('Brain Volume')
    ax.grid(True)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles[:2], labels=labels[:2], title='Sex')

    # Add explanation text below the plot
    plt.figtext(0.13, 0.32,  f"This scatter plot shows the relationship between age and total intracranial volume, \n"
                            f"with a cubic polynomial fit. The trend is separated by sex, and confidence intervals \n"
                            f"are included for each fit.\nData points outside the initial study {threshold} IQR range are excluded from the plot.\n\n"
                            f"Plot limits set to {age_min}-{age_max} months, n = {n}.\n"
                            f"Included projects = {', '.join(project_labels)}",
                wrap=True, horizontalalignment='left', fontsize=12,
                bbox={'facecolor': 'lightgray', 'alpha': 0.5, 'pad': 15})  # Added padding for better spacing

    # Adjust layout to ensure no overlap
    plt.subplots_adjust(top=0.85, bottom=0.2)  # Adjust to fit title and text properly

    plot_path = os.path.join(workdir, "ageVol_scatter_plot.png")
    plt.savefig(plot_path)
    #pdf.savefig()  # Save plot and text to the PDF
    plt.close()

    pdf.drawImage(plot_path, 75, next_y_coordinate, width= 400, preserveAspectRatio=True)   # Position plot higher on the page    

    
    volumetrics_to_plot = ['total cerebral white matter', 'total cerebral cortex', 'hippocampus', 
                   'thalamus', 'amygdala', 'putamen', 'caudate']

    pairs = list(itertools.combinations(labels, 2))
    # grouped = df.groupby(['sex','age_group'])

    # # Set up the figure and axes for a grid layout
    # fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(15, 12))  # Adjust as needed
    # axes = axes.flatten()

    # for i,col in enumerate(volumetrics_to_plot):

    #     # Calculate mean and std for each group
    #     df[f'mean_{col}'] = grouped[col].transform('mean')
    #     df[f'std_{col}'] = grouped[col].transform('std')

    #     # Calculate z-scores
    #     df[f'z-score_{col}'] = (df[col] - df[f'mean_{col}']) / df[f'std_{col}']

    #     sns.boxplot(x='age_group', y=f'z-score_{col}', data=df, ax=axes[i], order=used_age_groups, palette='Set2',showfliers=False)
    #     # add_stat_annotation(axes[i], data=df, x='age_group', y=f'z_score_{col}',
    #     #                 box_pairs=pairs, test='t-test_ind', text_format='star',
    #     #                 loc='inside', verbose=2)
        
    #     axes[i].set_xticklabels( age_group_labels, rotation=60)
    #     axes[i].set_title(col.title())
    #     axes[i].set_xlabel('Age Group')
    #     axes[i].set_ylabel((f'z-score_{col}').replace('_',' ').title())

    # for j in range(len(volumetrics_to_plot), len(axes)):
    #     fig.delaxes(axes[j])

    # # Adjust layout
    # plt.tight_layout()
    # plt.savefig(os.path.join(workdir,"volumetrics.png"))
    
    pdf = beautify_report(pdf,False,True)
    pdf.showPage()

    #### Show an example of a few segmentations
    
    pdf.save()  # Save the PDF

    print("PDF summary report has been generated.")
    return report

# 4. Generate the QC report
def generate_qc_report (input_dir, input_labels,project_labels) :

    """Generate the QC report section in a PDF format.

    Returns: report filename
        
    """
    filename = "qc_report"
    report = f'{workdir}{filename}.pdf'
    pdf = canvas.Canvas((f'{workdir}{filename}.pdf') )
    pdf = beautify_report(pdf,False,True)

    a4_fig_size = (8.27, 11.69)  # A4 size

    if input_labels['qc'] != "":
        df = pd.read_csv(os.path.join(input_dir,input_labels['qc']))
        #Columns of interest
        cols = ["quality_AXI", "quality_COR","quality_SAG","QC_all"]

        # Define the color palette depending on the attribute
        color_palette = {
            'good': '#6D9C77',  # Cool-toned green
            'passed': '#6D9C77',  # Cool-toned green

            'failed': '#D96B6B',  # Muted, elegant red
            'bad': '#D96B6B',  # Muted, elegant red

            'unsure': '#E7C069',  # Soft, subtle yellow
            'incomplete': '#6A89CC'  # Muted blue
        }


        # Pie chart for each acquisition type
        for col in cols:
            counts = df[col].value_counts()  # Count 'pass', 'fail', 'unclear' in each column
            # Extract colors based on labels present in the column
            
            colors = [color_palette[label] for label in counts.index if label in color_palette]
            plt.figure(figsize=(8, 8))
            plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90,colors=colors,wedgeprops={'edgecolor': 'black', 'linewidth': 1},textprops={'fontsize': 12} )
            plt.title(f'QC Distribution for {col}',fontsize=14)
            plot_path = os.path.join(workdir, f"{col}.png")
            # plt.tight_layout()
            plt.savefig(plot_path)
            plt.close()

        # Define subtitle text and positioning
        subtitle_text = "Quality Control Distribution by Acquisition Type"
        subtitle_x = A4[0] / 2  # Centered horizontally
        subtitle_y = 27 * cm  # Position the subtitle near the top in cm

        # Draw the subtitle
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(subtitle_x, subtitle_y, subtitle_text)

        # Define image positions for a 2x2 grid using cm units
        positions = [
        (1 * cm, 16 * cm),   # Top-left (lowered)
        (10 * cm, 16 * cm),  # Top-right (lowered)
        (1 * cm, 7 * cm),    # Bottom-left (lowered)
        (10 * cm, 7 * cm)    # Bottom-right (lowered)
    ]

        # Define position for the line chart below the grid
        line_chart_position = (1 * cm, 5 * cm)  # Adjust this y-coordinate as necessary

        # Load and draw each saved pie chart image at the specified positions
        for i, col in enumerate(cols):
            img = ImageReader(os.path.join(workdir, f"{col}.png"))
            x, y = positions[i]
            pdf.drawImage(img, x, y, width=10 * cm, height=10 * cm)  # Adjust image size as needed
        
        
        
        ####### Failures over time ########

            # Preprocess the session_date to replace underscores with colons
        df['session_date'] = df['Session Label'].str.replace('_', ':', regex=False)

        # Ensure session_date is a datetime type
        df['session_date'] = pd.to_datetime(df['session_date'], errors='coerce')

        #Check for any parsing issues
        if df['session_date'].isnull().any():
            print("Warning: Some dates could not be parsed.")

        # Extract month and year for monthly grouping
        df['month'] = df['session_date'].dt.to_period('M')

        # Count total entries and failures by month
        total_by_month = df.groupby('month').size()
        failures_by_month = df[df['QC_all'] == 'failed'].groupby('month').size()

        # Calculate percentage of failures
        failure_percentage_monthly = (failures_by_month / total_by_month) * 100

        # Plotting setup
        fig = plt.figure(figsize=a4_fig_size)
        ax = fig.add_axes([0.125, 0.5, 0.8, 0.4])  # Position and size of the plot within the A4 page

        # Use seaborn's lineplot on ax
        sns.lineplot(
            x=failure_percentage_monthly.index.astype(str), 
            y=failure_percentage_monthly.values, 
            marker='o', linestyle='-', color='#D96B6B', ax=ax
        )

        # Set title and labels directly on ax
        ax.set_title('Monthly Percentage of QC Failures')
        ax.set_xlabel('Year-Month')
        ax.set_ylabel('Percentage of Failures (%)')
        ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels for readability
        ax.grid(True)

        

        # Add explanation text just below the plot within the figure
        plt.figtext(
            0.17, 0.32,  # Position relative to the figure (0.42 keeps it below ax)
            "This line chart illustrates the monthly failure rate\nfor quality control (QC) across sessions,\n"
            "shown as a percentage of total acquisitions for each month.\n\n"
            f"Included projects = {', '.join(project_labels)}",
            wrap=True, horizontalalignment='left', fontsize=12,
            bbox={'facecolor': 'lightgray', 'alpha': 0.5, 'pad': 10}
        )
        
        plt.tight_layout()  # Adjust layout to make room for rotated labels   
        plot_path = os.path.join(workdir,"failure_percentage_over_time.png")
        plt.savefig(plot_path)  # Save the plot as an image
        
        pdf.showPage() #new page        

        # Position line chart image below the grid of pie charts
        pdf.drawImage(plot_path,  70, -20, width= 400, preserveAspectRatio=True)

    
    else:
        # Define subtitle text and positioning
        subtitle_text = "No QC input was provided."
        subtitle_x = A4[0] / 2  # Centered horizontally
        subtitle_y = 27 * cm  # Position the subtitle near the top in cm

        # Draw the subtitle
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(subtitle_x, subtitle_y, subtitle_text)

    
    pdf.save()

    return report

# 5. Merge the Cover Page and Data Report
def merge_pdfs(cover, report, final_report):
    merger = PdfMerger()

    print("Merging the cover page and data report...")
    print("Cover Page: ", cover)
    print("Data Report: ", report)
    #print("QC Report: ", qc)
    print("Final Report: ", final_report)

    # Append the cover page
    merger.append(cover)

    # Append the data report
    merger.append(report)

    # Append the qc report
    # merger.append(qc)

    # Write to a final PDF
    merger.write(final_report)
    merger.close()
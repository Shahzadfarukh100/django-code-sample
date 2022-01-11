from django.http import HttpResponse
from datetime import datetime
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils import timezone

import fpdf

min_font_size = 8

savvy_r = 182
savvy_g = 40
savvy_b = 32

class PdfReport(): # pragma: no cover
    def __init__(self, flight_reports, ticket_body):
        self.flight_reports = flight_reports
        self.response = HttpResponse(content_type='application/pdf')
        self.ticket_body = ticket_body

        # self.canvas = canvas.Canvas(self.response, pagesize=letter)
        # self.width, self.height = letter


    def _title(self):
        ## Logo
        self.pdf.image(settings.PROJECT_DIR + '/templates/analyst/SavvyLogo.jpg', 1, 0.76, 6, 1.44)

        ## Title
        self.pdf.set_font('DejaVuBold','',16)
        self.pdf.set_text_color(54, 95, 145)
        self.pdf.set_xy(10.7, 0.9)
        self.pdf.cell(10, 0, "Engine Monitor Data", align='R')
        self.pdf.set_xy(10.7, 1.6)
        self.pdf.cell(10, 0, "Analysis Report", align="R")


        # self.pdf.image(settings.PROJECT_DIR + '/templates/analyst/sigmund_head.jpg', 19, 0.25, 1.5, 1.935)

        self.pdf.line(1, 2.2, 20.59, 2.2)
        return 2.2

    def _date_only(self, a_date):
        return a_date.strftime("%Y-%m-%d")

    def _header(self, start_height, flight_report):

        column_width = 6.53
        row_height = 0.5
        margin = 0.5
        gap = 0.2
        self.pdf.set_text_color(0, 0, 0)

        def create_set(head1, head2, head3, row1, row2, row3, h_offset):
            self.pdf.set_font('DejaVuBold','', 12)

            w1 = self.pdf.get_string_width(head1)
            w2 = self.pdf.get_string_width(head2)
            w3 = self.pdf.get_string_width(head3)

            offset = max([w1, w2, w3])

            self.pdf.set_xy(h_offset + 1, start_height)
            self.pdf.cell(offset, 0, head1, ln=1)
            self.pdf.set_xy(h_offset + 1, start_height + row_height)
            self.pdf.cell(offset, 0, head2, ln=1)
            self.pdf.set_xy(h_offset + 1, start_height + 2 * row_height)
            self.pdf.cell(offset, 0, head3, ln=1)

            remaining_width = column_width - offset - margin - gap

            f1 = self._font_size_to_fit(row1, min_font_size, 12, remaining_width if w1 != 0 else column_width - margin)
            f2 = self._font_size_to_fit(row2, min_font_size, 12, remaining_width if w2 != 0 else column_width - margin)
            f3 = self._font_size_to_fit(row3, min_font_size, 12, remaining_width if w3 != 0 else column_width - margin)

            smallest_font = min([f1, f2, f3])
            self.pdf.set_font('DejaVu', '', smallest_font)

            r1 = self._crop_text_to_fit(row1, smallest_font, remaining_width if w1 != 0 else column_width - margin, 1)
            r2 = self._crop_text_to_fit(row2, smallest_font, remaining_width if w2 != 0 else column_width - margin, 1)
            r3 = self._crop_text_to_fit(row3, smallest_font, remaining_width if w3 != 0 else column_width - margin, 1)

            self.pdf.set_xy(h_offset + 1 + (offset+gap if w1 != 0 else 0), start_height)
            self.pdf.cell(remaining_width if w1 != 0 else column_width-margin, 0, r1, ln=1)
            self.pdf.set_xy(h_offset + 1 + (offset+gap if w2 != 0 else 0), start_height + row_height)
            self.pdf.cell(remaining_width if w1 != 0 else column_width-margin, 0, r2, ln=1)
            self.pdf.set_xy(h_offset + 1 + (offset+gap if w3 != 0 else 0), start_height + 2 * row_height)
            self.pdf.cell(remaining_width if w1 != 0 else column_width-margin, 0, r3, ln=1)


        head1 = "Client:"
        head2 = "Aircraft:"
        head3 = "Flight:"

        this_flight = flight_report.flight

        row1 = "%s %s" % (this_flight.aircraft.user.first_name, this_flight.aircraft.user.last_name )
        row2 = "%s" % this_flight.aircraft.registration_no
        row3 = "%s" % self._date_only(this_flight.date)

        create_set(head1, head2, head3, row1, row2, row3, 0)

        head1 = "A/C Type:"
        head2 = "Engine:"
        head3 = "Monitor:"

        row1 = "%s %s" % (this_flight.aircraft.aircraft_manufacturer.name if this_flight.aircraft.aircraft_manufacturer is not None else "", this_flight.aircraft.aircraft_model.name if this_flight.aircraft.aircraft_model is not None else "")
        row2 = "%s %s" % (this_flight.aircraft.engine_manufacturer.name if this_flight.aircraft.engine_manufacturer is not None else "", this_flight.aircraft.engine_model.name if this_flight.aircraft.engine_model else "")
        row3 = "%s %s" % (this_flight.aircraft.engine_monitor_manufacturer.name if this_flight.aircraft.engine_monitor_manufacturer else "", this_flight.aircraft.engine_monitor_model.name if this_flight.aircraft.engine_monitor_model else "" )

        create_set(head1, head2, head3, row1, row2, row3, column_width)

        head1 = "Report Date:"
        head2 = ""


        if flight_report.engine == 0:
            head3 = ""
            row1 = "%s" % self._date_only(datetime.utcnow())
            if this_flight.aircraft.current_subscription() is not None:
                row2 = "Subscr. ends: %s" % self._date_only(this_flight.aircraft.current_subscription().end_date)
                row3 = ""
            else:
                row2 = "SavvyMx client"
                row3 = ""
        else:
            head3 = "Engine Position:"
            row1 = "%s" % self._date_only(datetime.utcnow())
            if this_flight.aircraft.current_subscription() is not None:
                row2 = "Subscr. ends: %s" % self._date_only(this_flight.aircraft.current_subscription().end_date)
            else:
                row2 = "SavvyMx client"
            row3 = "Left" if flight_report.engine == 1 else "Right"

        create_set(head1, head2, head3, row1, row2, row3, column_width * 2)

        return start_height + 3 * row_height

    def _font_size_to_fit(self, text, minimum, maximum, width):
        font_size = maximum
        while True:
            self.pdf.set_font_size(font_size)
            if self.pdf.get_string_width(text) <= width:
                break
            if font_size <= minimum:
                return font_size
            else:
                font_size = max(font_size-1, minimum)
            if text == "":
                break

        return font_size

    def _crop_text_to_fit(self, text, font_size, line_width, line_count):

        self.pdf.set_font_size(font_size)
        resulting_lines = [""]
        remaining_lines = line_count
        remaining_line_space = line_width
        words = text.split(' ')
        current_word = 0

        while remaining_lines > 0 and current_word < len(words):
            word_width = self.pdf.get_string_width(words[current_word] + " ")
            if word_width <= remaining_line_space - 0.2:
                remaining_line_space -= word_width
                resulting_lines[-1] += words[current_word] + " "
                current_word += 1
            else:
                resulting_lines[-1] = resulting_lines[-1].strip()
                resulting_lines.append("")
                remaining_lines -= 1
                remaining_line_space = line_width

        if resulting_lines[-1] == "":
            resulting_lines = resulting_lines[0:-1]

        if remaining_lines == 0 and current_word < len(words):
            resulting_lines[-1] += " "  + words[current_word]
            while True:

                if self.pdf.get_string_width(resulting_lines[-1]) + 0.2 < line_width:
                    break

                if resulting_lines[-1] == "...":
                    break
                elif resulting_lines[-1].endswith('...'):
                    resulting_lines[-1] = resulting_lines[-1][0:-4]
                else:
                    resulting_lines[-1] = resulting_lines[-1][0:-1]
                resulting_lines[-1] += "..."

        return_text = "\n".join(resulting_lines)
        return return_text.strip()

    def _section_heading(self, x, y, text):
        self.pdf.set_font('DejaVuBold','', 10)
        self.pdf.set_xy(x, y)
        self.pdf.set_fill_color(0, 0, 0)
        self.pdf.set_text_color(255, 255, 255)
        width = self.pdf.get_string_width(text) + 0.2
        height = 0.5
        self.pdf.cell(width, height, text, fill=1)
        return height + 0.1

    def _section_text(self, x, y, text):

        font_size = self._font_size_to_fit(text, min_font_size, 12, 19.59 * 5)
        self.pdf.set_font('DejaVu', '', font_size)
        text = self._crop_text_to_fit(text, font_size, 19.59, 5)

        self.pdf.set_font('DejaVu', '', font_size)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.set_xy(x, y)
        self.pdf.multi_cell(19.59, 0.38, text, align="L")


        return 2

    def _traffic(self, x, y, value, gami = False):
        self.pdf.set_font('DejaVuBold','', 10)
        self.pdf.set_text_color(0, 0, 0)
        padding = 0.5


        if value == "Satisfactory":
            self.pdf.set_fill_color(0, 255, 0)
        elif value == "Caution":
            self.pdf.set_fill_color(255, 230, 48)
        elif value == "Alert":
            self.pdf.set_fill_color(255, 115, 115)
        elif value == "0" or value == "N/A":
            self.pdf.set_fill_color(230, 230, 230)
            value = "Not Applicable" if not gami else "N/A (no usable mixture sweeps observed)"

        width = self.pdf.get_string_width(value)
        self.pdf.set_xy(x - width - padding, y)

        self.pdf.cell(width + padding, 0.5, value, align="C", fill= 1)



    def _data_box(self, x, y, title, summary, data ):
        self._section_heading(x, y, title )
        self._traffic(x + 9.295, y, summary)
        width = (21.59 - 3) / 2
        offset = 0.7
        title_font_size = 8

        min_font = 100

        # Figure out what the minimum size is, in order to fit the biggest line
        for line in data:
            self.pdf.set_font('DejaVuBold','', title_font_size)
            title_width = self.pdf.get_string_width(line[0])
            remaining_space = width - title_width
            font_size = self._font_size_to_fit(line[1], min_font_size, 12, remaining_space)
            if font_size < min_font:
                min_font = font_size

        # Using said size, go crop all the lines to fit
        for line in data:
            self.pdf.set_font('DejaVuBold','', title_font_size)
            title_width = self.pdf.get_string_width(line[0])
            remaining_space = width - title_width
            self.pdf.set_font('DejaVu', '', min_font)
            line[1] = self._crop_text_to_fit(line[1], min_font, remaining_space, 1)

        # Now display everything
        for line in data:
            self.pdf.set_xy(x, y + offset)
            self.pdf.set_font('DejaVuBold','', title_font_size)
            self.pdf.set_text_color(0, 0, 0)
            title_width = self.pdf.get_string_width(line[0])
            self.pdf.cell(title_width, 0.4, line[0])

            self.pdf.set_font('DejaVu', '', min_font)
            self.pdf.cell(0, 0.4, line[1])
            offset += 0.45

    def _gami_box(self, top, index, title, content, crop = False):
        box_margin = 1
        box_width = (21.59 - 2 - box_margin * 3) / 4

        x = 1 + max(0, index - 1) * ( box_width + box_margin)
        self.pdf.set_xy(x, top)
        self.pdf.set_font('DejaVuBold','', 10)
        self.pdf.cell(box_width, 0.3, title)

        self.pdf.set_xy(x, top + 0.3)
        self.pdf.set_font('DejaVu', '', 10)
        if crop:
            content = self._crop_text_to_fit(content, 10, box_width, 9)
        self.pdf.multi_cell(box_width, 0.4, content, align="L")

        if index != 4:
            self.pdf.line(x + box_width + box_margin * 0.5, top, x + box_width + box_margin * 0.5, top + 3.5 )

    def add_explanation(self):

        def explanation_title(title):
            self.pdf.set_text_color(54, 95, 145)
            self.pdf.set_font('DejaVuBold','',14)
            self.pdf.write(0.45, title)
            self.pdf.ln(0.45 + 0.1)

        def explanation_subtitle(title, text):

            title += ":  "

            line_height = 0.42

            self.pdf.set_text_color(54, 95, 145)
            self.pdf.set_font('DejaVuBold','',10)
            self.pdf.write(line_height, title)

            self.pdf.set_text_color(0,0,0)
            self.pdf.set_font('DejaVu','',10)
            self.pdf.write(line_height, text)

            self.pdf.ln(line_height + 0.2)

        def explanation_text(text, border = False):

            line_height = 0.42

            self.pdf.set_text_color(0,0,0)
            self.pdf.set_font('DejaVu','',10)
            self.pdf.write(line_height, text)
            self.pdf.ln(line_height + 0.3)



        def box_text(text):

            self.pdf.set_text_color(0,0,0)
            self.pdf.set_font('DejaVu','',10)
            self.pdf.multi_cell(19.59, 0.42, text, align='L', border = 1 )


        self.pdf.add_page()
        self.pdf.set_margins(1, 1, 1)

        self.pdf.image(settings.PROJECT_DIR + '/templates/analyst/SavvyLogo.jpg', 1, 0.3, 6, 1.44)

        ## Title
        self.pdf.set_font('DejaVuBold','',14)
        self.pdf.set_text_color(savvy_r, savvy_g, savvy_b)
        top = 1.1
        self.pdf.set_xy(8.8, top)
        self.pdf.cell(21.59, 0, "Savvy Aviation, Inc.", align='L')

        top += 0.6
        self.pdf.set_text_color(95, 95, 95)
        self.pdf.set_xy(8.8, top)
        self.pdf.set_font('DejaVuBold','',12)
        self.pdf.cell(21.59, 0, "30 N. Gould St, Suite 7491, Sheridan, WY 82801", align='L')

        top += 0.5
        self.pdf.set_text_color(54, 95, 145)
        self.pdf.set_xy(1, top)
        self.pdf.set_font('DejaVuBold','',16)
        self.pdf.write(0.5, "Explanation of Engine Monitor Data Analysis Report")
        self.pdf.ln(0.6)

        self.pdf.set_text_color(0, 0, 0)
        self.pdf.set_font('DejaVu','',10)
        self.pdf.write(0.5, "Copyright 2018 Savvy Aircraft Maintenance Management, Inc. All rights reserved.")
        self.pdf.ln(0.9)

        explanation_title("Glossary of Abbreviations")

        def abbreviation(column_width, column_top, left, name, text, font_size = 10):
            line_height = 0.45
            self.pdf.set_text_color(0, 0, 0)
            self.pdf.set_font('DejaVuBold','',font_size)
            self.pdf.set_xy(left, column_top)
            self.pdf.cell(column_width, line_height, name)
            width = self.pdf.get_string_width(name)

            self.pdf.set_font('DejaVu','',font_size)
            self.pdf.set_xy(left + width + 0.1, column_top)
            self.pdf.cell(column_width - width - 0.1, line_height, text)

            return line_height

        top += 2


        column_margin = 0.2


        column_top = top
        column_left = 1
        column_width = 5.5
        column_top += abbreviation(column_width, column_top, 1, "EGT", "- Exhaust Gas Temperature")
        column_top += abbreviation(column_width, column_top, 1, "CHT", "- Cylinder Head Temperature")
        column_top += abbreviation(column_width, column_top, 1, "TIT", "- Turbine Inlet Temperature")
        column_top += abbreviation(column_width, column_top, 1, "MAP", " - Manifold Pressure")

        column_top = top
        column_left += column_margin + column_width
        column_width = 5.9
        column_top += abbreviation(column_width, column_top, column_left, "RPM", " - Revolutions Per Minute")
        column_top += abbreviation(column_width, column_top, column_left, "FF", " - Fuel flow")
        column_top += abbreviation(column_width, column_top, column_left, "GPH/PPH", " - Gallons/Pounds Per Hr.")
        column_top += abbreviation(column_width, column_top, column_left, "ROP/LOP", " - Rich/Lean of Peak EGT")

        column_top = top
        column_left += column_margin + column_width
        column_width = 6
        column_top += abbreviation(column_width, column_top, column_left, "EGTn/CHTn", " - EGT/CHT cylinder #n")
        column_top += abbreviation(column_width, column_top, column_left, "", "Cyl #1 is right rear on Continental, right front on Lycoming,", font_size=8)
        column_top += abbreviation(column_width, column_top, column_left, "", "odd #s on right, even #s on left (as seen from the cockpit).", font_size=8)
        column_top += abbreviation(column_width, column_top, column_left, "GAMI", " - General Aviation Modifications, Inc.")
        column_top += abbreviation(column_width, column_top, column_left, "T/O", " - Takeoff")


        self.pdf.set_xy(1, column_top+0.2)
        explanation_title("Client Comments Section")
        explanation_text("In this section, the analyst records any relevant client comments pertaining to the analysis. This might include the client's stated reason for requesting the analysis, description of the flight (including any flight test profile protocols flown), description of observed symptoms or abnormal indications (if any), etc.")

        explanation_title("Summary of Findings Section")
        explanation_text("In this section, the analyst provides a concise summary of analytical findings, with special emphasis on items that the analyst considers particularly significant, abnormal, or suboptimal. (Much more detail about these findings appears in the next section of the report.)")

        explanation_title("Analysis Detail Section")
        explanation_text("In this section, the analyst provides detailed analytical findings in each of seven specific functional areas. The findings for each of these areas are color-coded to indicate whether the analysis considers them to be Satisfactory, Caution, Alert, or Not Applicable. (\"Not applicable\" generally indicates that the engine monitor data necessary to assess a functional area is either missing or inadequate. Not all engine monitors are capable of capturing the data required to analyze some of these areas.)")
        explanation_subtitle("GAMI Lean Test", "An analysis of mixture distribution quality: the extent to which all cylinders are operating at the same mixture. The \"GAMI spread\" (measured in term of fuel flow) indicates the mixture difference between the leanest- and richest-running cylinder. (For fuel-injected engines, a GAMI spread of 0.5 GPH or less is desirable.) This test requires that the engine monitor is capable of recording fuel flow and that the flight includes one or more \"mixture sweeps\" performed per Savvy's flight test protocol.")
        explanation_subtitle("Ignition", "An analysis of ignition system performance: magneto condition, magneto timing, spark plug condition, and ignition harness condition. This test requires that the flight include an \"ignition system stress test\" (lean in-flight mag check) performed per Savvy's flight test protocol.")
        explanation_subtitle("Max Power", "An analysis of key performance-related parameters -- fuel flow, manifold pressure, and RPM -- at full takeoff power. This test requires that the engine monitor is capable of recording these parameters.")
        explanation_subtitle("Temperatures", "An analysis of key temperature parameters -- CHTs, EGTs and (for turbos) TITs -- during all phases of the flight. Significant exceedences are noted. (Temperature control is the key to engine longevity.)")
        explanation_subtitle("Engine Monitor", "A performance evaluation of the engine monitor instrumentation itself. Any faulty sensors, harness and connector problems, noisy data, and system configuration errors will be noted here.")
        explanation_subtitle("Powerplant Management", "An evaluation of the pilot's powerplant management procedures. This could include power settings, leaning technique, and compliance with Savvy's flight test profile protocols.")
        explanation_subtitle("Electrical", "An analysis of the aircraft electrical system performance, including alternators, batteries, regulators/control units, etc. (Not all engine monitors record this information.)")

        explanation_title("Recommendations Section")
        explanation_text("In this section, the analyst may offer recommendations and suggestions for actions to be taken to remediate any less-than-satisfactory items identified by the analysis. These could include engine adjustments, preventive maintenance tasks, and/or changes to the pilot's powerplant management techniques.")

        box_text("CAUTION: Savvy-recommended engine adjustments and maintenance actions should be made only after consultation with a certificated mechanic or repair station. Savvy-recommended changes to powerplant management techniques must be implemented in compliance with the limitations section of the aircraft's Pilots Operating Handbook (POH) or Airplane Flight Manual (AFM) and the engine manufacturer's Operators Manual (or equivalent document).")

    def additional(self, additional):
        self.pdf.add_page()
        self.pdf.set_margins(1, 1, 1)

        self.pdf.image(settings.PROJECT_DIR + '/templates/analyst/SavvyLogo.jpg', 1, 0.3, 6, 1.44)

        ## Title
        self.pdf.set_font('DejaVuBold','',14)
        self.pdf.set_text_color(savvy_r, savvy_g, savvy_b)
        top = 1.1
        self.pdf.set_xy(8.8, top)
        self.pdf.cell(21.59, 0, "Savvy Aviation, Inc.", align='L')

        top += 0.6
        self.pdf.set_text_color(95, 95, 95)
        self.pdf.set_xy(8.8, top)
        self.pdf.set_font('DejaVuBold','',12)
        self.pdf.cell(21.59, 0, "30 N. Gould St, Suite 7491, Sheridan, WY 82801", align='L')

        top += 0.8
        self.pdf.set_text_color(54, 95, 145)
        self.pdf.set_xy(1, top)
        self.pdf.set_font('DejaVuBold','',16)
        self.pdf.write(0.5, "Additional Remarks")
        self.pdf.ln(0.9)

        def explanation_text(text, border = False):

            line_height = 0.42

            self.pdf.set_text_color(0,0,0)
            self.pdf.set_font('DejaVu','',10)
            self.pdf.write(line_height, text)
            self.pdf.ln(line_height + 0.3)

        explanation_text(additional)


    def generate(self, attachment):

        first_flight = self.flight_reports.first().flight

        if attachment == '1':
            file_name = 'attachment; filename="%s %s %s %s.pdf"' % (self._date_only(datetime.utcnow()), first_flight.aircraft.user.first_name.strip().replace("\"", ''), first_flight.aircraft.user.last_name.strip().replace("\"", ''), first_flight.aircraft.registration_no)
            self.response['Content-Disposition'] = file_name.encode("ascii", "replace").replace(b"?", b"X")
        fpdf.set_global('FPDF_FONT_DIR', str(settings.PROJECT_DIR.ancestor(1).child('fonts')) )
        fpdf.set_global('FPDF_CACHE_MODE', 1)


        self.pdf = fpdf.FPDF('P', 'cm', 'Letter')


        self.pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.pdf.add_font('DejaVuBold', '', 'DejaVuSansCondensed-Bold.ttf', uni=True)

        self.pdf.set_auto_page_break(0)


        for flight_report in self.flight_reports:

            if not flight_report.not_empty():
                continue

            self.pdf.add_page()
            self.pdf.set_margins(1, 1, 1)

            # Title
            top = self._title()

            # Client Header
            top = self._header(top + 0.4, flight_report)

            # Client Comments
            self.pdf.line(1, top, 20.59, top)
            top += self._section_heading(1, top, "Client Comments")
            if self.ticket_body is not None:
                top += self._section_text(1, top, self.ticket_body.replace('\n', ' '))
            else:
                if flight_report.client_comments is None:
                    top += self._section_text(1, top, smart_str("N/A"))
                else:
                    top += self._section_text(1, top, smart_str(flight_report.client_comments.replace('\n', ' ')))

            # Summary of Findings

            self.pdf.line(1, top, 20.59, top)
            top += 0.1

            top += self._section_heading(1, top, "Summary of Findings")
            top += self._section_text(1, top, flight_report.findings.replace('\n', ' '))

            # GAMI Test

            self.pdf.line(1, top, 20.59, top)
            top += 0.1

            gami_top = top
            top += self._section_heading(1, top, "GAMI Lean Test")

            self._traffic(20.59, gami_top, flight_report.gami_summary, gami=True)

            self._gami_box(top, 1, "Sweep #1", flight_report.gami1)
            self._gami_box(top, 2, "Sweep #2", flight_report.gami2)
            self._gami_box(top, 3, "Sweep #3", flight_report.gami3)
            self._gami_box(top, 4, "Observations", flight_report.gami4.replace('\n', ' '), crop=True)
            top += 4

            # Data Boxes
            right_offset = 9.795 + 0.5
            box_height = 2.8
            line_top_adjust = 0.1
            line_bottom_adjust = 0.5

            self.pdf.line(1, top, 20.59, top)
            top += 0.1

            data = list()
            data.append ([ flight_report._meta.get_field('ignition1').verbose_name + ": ", flight_report.ignition1 ])
            data.append ([ flight_report._meta.get_field('ignition2').verbose_name + ": ", flight_report.ignition2 ])
            data.append ([ flight_report._meta.get_field('ignition3').verbose_name + ": ", flight_report.ignition3 ])
            data.append ([ flight_report._meta.get_field('ignition4').verbose_name + ": ", flight_report.ignition4 ])
            self._data_box(1, top, "Ignition", flight_report.ignition_summary, data )

            data = list()
            data.append ([ flight_report._meta.get_field('power1').verbose_name + ": ", flight_report.power1 ])
            data.append ([ flight_report._meta.get_field('power2').verbose_name + ": ", flight_report.power2 ])
            data.append ([ flight_report._meta.get_field('power3').verbose_name + ": ", flight_report.power3 ])
            data.append ([ flight_report._meta.get_field('power4').verbose_name + ": ", flight_report.power4 ])
            self._data_box(1 + right_offset, top, "Max Power", flight_report.power_summary, data )

            self.pdf.line(21.59 / 2, top + line_top_adjust, 21.59 / 2, top + box_height - line_bottom_adjust)

            top += box_height
            self.pdf.line(1, top - 0.2, 20.59, top - 0.2)
            data = list()
            data.append ([ flight_report._meta.get_field('temperatures1').verbose_name + ": ", flight_report.temperatures1 ])
            data.append ([ flight_report._meta.get_field('temperatures2').verbose_name + ": ", flight_report.temperatures2 ])
            data.append ([ flight_report._meta.get_field('temperatures3').verbose_name + ": ", flight_report.temperatures3 ])
            data.append ([ flight_report._meta.get_field('temperatures4').verbose_name + ": ", flight_report.temperatures4 ])
            self._data_box(1, top, "Temperatures", flight_report.temperatures_summary, data )

            data = list()
            data.append ([ flight_report._meta.get_field('monitor1').verbose_name + ": ", flight_report.monitor1 ])
            data.append ([ flight_report._meta.get_field('monitor2').verbose_name + ": ", flight_report.monitor2 ])
            data.append ([ flight_report._meta.get_field('monitor3').verbose_name + ": ", flight_report.monitor3 ])
            data.append ([ flight_report._meta.get_field('monitor4').verbose_name + ": ", flight_report.monitor4 ])
            self._data_box(1 + right_offset, top, "Engine Monitor", flight_report.monitor_summary, data )

            self.pdf.line(21.59 / 2, top + line_top_adjust, 21.59 / 2, top + box_height - line_bottom_adjust)

            top += box_height
            self.pdf.line(1, top - 0.2, 20.59, top - 0.2)
            data = list()
            data.append ([ flight_report._meta.get_field('powerplant1').verbose_name + ": ", flight_report.powerplant1 ])
            data.append ([ flight_report._meta.get_field('powerplant2').verbose_name + ": ", flight_report.powerplant2 ])
            data.append ([ flight_report._meta.get_field('powerplant3').verbose_name + ": ", flight_report.powerplant3 ])
            data.append ([ flight_report._meta.get_field('powerplant4').verbose_name + ": ", flight_report.powerplant4 ])
            self._data_box(1, top, "Powerplant Mgt", flight_report.powerplant_summary, data )

            data = list()
            data.append ([ flight_report._meta.get_field('electrical1').verbose_name + ": ", flight_report.electrical1 ])
            data.append ([ flight_report._meta.get_field('electrical2').verbose_name + ": ", flight_report.electrical2 ])
            data.append ([ flight_report._meta.get_field('electrical3').verbose_name + ": ", flight_report.electrical3 ])
            data.append ([ flight_report._meta.get_field('electrical4').verbose_name + ": ", flight_report.electrical4 ])
            self._data_box(1 + right_offset, top, "Electrical", flight_report.electrical_summary, data )

            self.pdf.line(21.59 / 2, top + line_top_adjust, 21.59 / 2, top + box_height - line_bottom_adjust)

            top += box_height
            self.pdf.line(1, top - 0.2, 20.59, top - 0.2)
            #top += 0.1

            top += self._section_heading(1, top, "Recommendations:")
            top += self._section_text(1, top, flight_report.recommendations.replace('\n', ' '))

            top += 1
            self.pdf.set_font('DejaVu', '', 8)
            self.pdf.set_xy(1, top)
            current_year = str(timezone.now().year)
            self.pdf.cell(20.59, 0.3, "Copyright 2012-{} by Savvy Aircraft Maintenance Management, Inc. All rights reserved.".format(current_year), align='C')

            if flight_report.additional is not None and flight_report.additional != "":
                self.additional(flight_report.additional)

        self.add_explanation()

        self.response.write(self.pdf.output('','S').encode('latin-1'))
        return self.response

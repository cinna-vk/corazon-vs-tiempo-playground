################################################################################
##
## Colorize Tool by Feniks (feniksdev.itch.io / feniksdev.com)
##
################################################################################
## This file contains code for an image recolouring tool. It requires three
## files to work:
## Image Tools for Ren'Py:
##      https://feniksdev.itch.io/image-tools-for-renpy
## Color Picker for Ren'Py:
##      https://feniksdev.itch.io/color-picker-for-renpy
## Better Colorize for Ren'Py:
##      https://feniksdev.itch.io/better-colorize-for-renpy
##
## I also highly recommend my Multi-Thumb Bar tool, found here:
##      https://feniksdev.itch.io/multi-thumb-bar-for-renpy
## It significantly cleans up the thresholds bar in the tool. You can pick it
## up as part of a bundle alongside the Colorize Tool Extras, which adds
## several quality-of-life features to this colorize tool.
##
## If you had previously downloaded any of those tools, you must have the most
## recent version as of 2023-11-12 for this tool to work, as they have all been
## updated with additional features to support this tool.
##
## These files are **required** for this tool to work.
##
## If you use these tools during development, credit me as Feniks @ feniksdev.com
##
## This tool is designed to be used during development only, and should be
## excluded from a proper build. The code to do so is included with this file.
##
## It also has a visual component, and includes in-game tutorials you can
## go through to learn how to use the tools.
## To access the tools, simply make yourself a button (probably on the main
## menu) that goes to the main tool screen, image_tools:
##
# textbutton "Image Tools" action ShowMenu("image_tools")
##
## Then you can select a tool and get started. You will be shown the tutorial
## the first time you use a tool.
## Leave a comment on the tool page on itch.io if you run into any issues!
################################################################################
## VARIABLES
################################################################################
## Persistent ##################################################################
################################################################################
## A set of the saved recolor tags.
default persistent.sprt_saved_recolor_tags = set()
## A set of "other" tags shown alongside the recoloured image.
default persistent.sprt_saved_other_tags = set()
## The current input in the "extra" input box (for additional images besides
## the main tag).
default persistent.sprt_extra = ""
## A dictionary of lists of the extra parts for a sprite.
default persistent.sprt_extra_list = dict()
## A set of extra layers which are currently not visible.
default persistent.sprt_hidden_extras = set()
## A dictionary mapping image tags to their threshold values and associated
## extra images.
default persistent.sprt_color_dict = dict()
## A dictionary of the properties for the comparison image.
default persistent.sprt_comparison_dict = dict()
## True if the different colours should blend along a gradient
default persistent.sprt_blend_gradient = True
## A set of tags that shouldn't be recoloured when used as extra images.
default persistent.sprt_recolor_extra_dict = set()
## The starting position of the draggable picker
default 40 persistent.sprt_colorize_xpos = config.screen_width-sprt.PICKER_FRAME_SIZE
default 40 persistent.sprt_colorize_ypos = sprt.SPACER*3
## Whether the RGB-recolorize mode is enabled
default persistent.sprt_rgb_recolorize_on = dict()
## Which channel the user is currently editing
default persistent.sprt_rgb_channel = "Gray"
## A dictionary saving the RGB and default channel values
default persistent.sprt_rgb_saved_colors = dict()
## The tutorial
default persistent.sprt_tutorial5_shown = False
## Normal ######################################################################
################################################################################
## A hexcode used for input to the picker.
default sprt.hexcode = "FFFFFF"
## Values used to determine the boundaries for each colour.
default sprt.thresholds = [255, 128, 0] + [0]*(MAX_COLORIZE_COLORS-3)
## The input field for entering thresholds.
default sprt.threshold_input = ""
## The number of shades used to recolour the image
default sprt.num_shades = 3
## Optional text saved with swatches so you can label them.
default sprt.swatch_text = ""
## The undo/redo history
default sprt.undo_history = list()
default sprt.redo_history = list()
## The current threshold/swatch state
default sprt.current_swatch_state = dict()
default sprt.current_threshold_state = dict()
## Lists of the redo/undo swatch history
default sprt.redo_list = list()
default sprt.undo_list = list()
## The input for an RGBColorize object.
default sprt.rgbc_input = ""
default sprt.rgbc_obj = None
################################################################################
## CONSTANTS
################################################################################
## The size of the colour picker. This is a percentage of the screen size,
## and it is square.
define sprt.PICKER_SIZE = min(
    int(config.screen_width*0.5),
    int(config.screen_height*0.5)
)
## The width of the picker bars.
define sprt.PICKER_BAR_WIDTH = int(sprt.PICKER_SIZE*0.09)
## The width of the swatch
define sprt.SWATCH_WIDTH = int(sprt.PICKER_SIZE/4)
define sprt.SWATCH_SQUARE_SIZE = int(sprt.PICKER_SIZE/8)
## The width of the frame holding the picker and associated bars
define 30 sprt.PICKER_FRAME_SIZE = (sprt.PICKER_SIZE+sprt.PADDING*36
    +sprt.PICKER_BAR_WIDTH
    +sprt.SWATCH_WIDTH)
## The maximum number of swatches we can fit widthwise into the frame,
## multiplied by five because there are five rows.
define 40 sprt.NUM_SAVED_SWATCHES = (
    sprt.PICKER_FRAME_SIZE // (sprt.XSPACER+int(sprt.PADDING*3.5))) * 5
## Set to True by the extras recolorize file
define -99 sprt.HAS_COLORIZE_EXTRAS = False
## The maximum number of things we can remember to undo/redo.
define sprt.MAX_UNDO_REDO = 10

## A blinking caret for the threshold and hexcode input
image sprt_caret:
    Solid("#000", xysize=(2, preferences.font_size),
        style='sprt_input_input', yalign=0.0)
    0.6
    Null()
    0.6
    repeat

################################################################################
## FUNCTIONS
################################################################################
init -80 python in sprt:
    from store import At, Color, Fixed, Text, Function, SetScreenVariable
    from store import DynamicDisplayable, MAX_COLORIZE_COLORS
    from store import RGBColorize

    ## INITIALIZATION FUNCTIONS ################################################
    def make_bars(picker):
        """
        Creates and returns a list of bar images for the picker. Bars use
        gradients to clarify the thresholds.
        """
        global persistent
        bars = [ ]
        bars.append(DynamicDisplayable(get_gradient_bar, picker=picker,
            left=0, right=0))
        for i in range(MAX_COLORIZE_COLORS):
            bars.append(DynamicDisplayable(get_gradient_bar, picker=picker,
                left=i, right=i+1))
        bars.append(DynamicDisplayable(get_gradient_bar, picker=picker,
            left=MAX_COLORIZE_COLORS-1, right=MAX_COLORIZE_COLORS-1))
        return bars

    def make_multibar(picker):
        """
        Creates and returns a MultiBar with the provided bars. In a try/except
        block to avoid errors for users who do not have MultiBar.
        """
        global persistent
        ## Bar images for the thresholds
        bars = make_bars(picker)
        ## Initial values for the multibar
        num_thumbs = fetch_initial_num_thumbs(persistent.sprt_who)
        start_vals = fetch_initial_start_values(persistent.sprt_who)
        try:
            from store import MultiBar
            return MultiBar(
                num_thumbs=num_thumbs,
                xysize=(PICKER_SIZE, PICKER_BAR_WIDTH),
                thumb_size=(PADDING*4, PICKER_BAR_WIDTH),
                bars=bars,
                idle_thumbs="selector_bg",
                insensitive_thumbs=construct_frame(RED, GRAY, PADDING),
                bar_range=255,
                start_values=start_vals,
                tracked_value="sprt.num_shades",
                changed=update_shader_values,
                released=record_threshold_state,
            )
        except Exception as e:
            print("EXCEPTION making multibar:", e)
            return Text("Multibar could not be created", style='sprt_text')

    def fetch_initial_num_thumbs(who):
        """
        Return the number of thumbs to display initially.
        """
        global persistent, num_shades

        args, kwargs = persistent.sprt_color_dict.get(who, ((), {}))
        if not args or not kwargs:
            num_shades = 3
            return 3
        num_shades = kwargs.get('num', 3)
        return kwargs.get('num', 3)

    def fetch_initial_start_values(who):
        """
        Return the spread of start values for the multi-bar.
        """
        global persistent, thresholds

        args, kwargs = persistent.sprt_color_dict.get(who, ((), {}))
        if not args or not kwargs:
            return [0, 50, 50, 0]

        if kwargs.get('rgb', False):
            ## RGB version
            ## What's the current channel?
            channel = persistent.sprt_rgb_channel
            ## Get the saved colours for this channel
            saved_colors = kwargs.get(channel, [])
            if saved_colors:
                thresholds = list(saved_colors[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2])
            else:
                thresholds = list(args[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2])
        else:
            thresholds = list(args[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2])

        change_num_shades(kwargs.get('num', 3), None)
        ret = set_mb_values(None, True)
        return ret

    def fetch_initial_colors(who):
        """
        Return the initial saved colours dictionary for the picker.
        """
        global persistent

        args, kwargs = persistent.sprt_color_dict.get(who, ((), {}))
        colors = ["#fff", "#888", "#000"] + ["#000"]*(MAX_COLORIZE_COLORS-3)
        ret = dict()
        if not args or not kwargs: ## No saved information
            for i in range(MAX_COLORIZE_COLORS):
                ret[i] = Color(colors[i])
            return ret

        if kwargs.get('rgb', False):
            ## RGB version
            ## What's the current channel?
            channel = persistent.sprt_rgb_channel
            ## Get the saved colours for this channel
            saved_colors = kwargs.get(channel, [])
            for i, col in enumerate(saved_colors[:MAX_COLORIZE_COLORS]):
                ret[i] = Color(col)
        if not ret:
            for i, col in enumerate(args[:MAX_COLORIZE_COLORS]):
                ret[i] = Color(col)

        return ret

    ## COPY FUNCTIONS ##########################################################

    def copy_colors_to_clipboard(picker):
        """
        Copies the current colour values from the picker and the
        current thresholds to the clipboard for use with the multi_colorize
        function.
        """
        global num_shades, thresholds

        if persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False):
            ## 4-channel version
            save_current_rgb_channel(picker)
            red = persistent.sprt_rgb_saved_colors.get(persistent.sprt_who, dict()).get("Red", [])
            green = persistent.sprt_rgb_saved_colors.get(persistent.sprt_who, dict()).get("Green", [])
            blue = persistent.sprt_rgb_saved_colors.get(persistent.sprt_who, dict()).get("Blue", [])
            gray = persistent.sprt_rgb_saved_colors.get(persistent.sprt_who, dict()).get("Gray", [])

            red_num = red[-1] if len(red) > MAX_COLORIZE_COLORS*2 else num_shades
            green_num = green[-1] if len(green) > MAX_COLORIZE_COLORS*2 else num_shades
            blue_num = blue[-1] if len(blue) > MAX_COLORIZE_COLORS*2 else num_shades
            gray_num = gray[-1] if len(gray) > MAX_COLORIZE_COLORS*2 else num_shades


            recol = RGBColorize(gray[:gray_num],
                gray[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS+gray_num],
                red[:red_num],
                red[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS+red_num],
                green[:green_num],
                green[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS+green_num],
                blue[:blue_num],
                blue[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS+blue_num])
        else:
            recol = RGBColorize([picker.get_color(i) for i in range(num_shades)],
                thresholds[:num_shades])

        ret = recol.pretty_print()

        copy_to_clipboard(ret)

    def copy_color(picker, num):
        """
        Copies the colour code from the picker at num to the clipboard.
        """
        copy_to_clipboard('"{}"'.format(picker.get_color(num).hexcode))

    ## SAVE/LOAD FUNCTIONS #####################################################

    def record_colorize_drag_pos(drags, drop):
        """
        Remember where the box with the colour picker was dragged to.

        Parameters:
        -----------
        drags : Drag[]
            A list of Drag objects (which will contain one Drag, the window).
        drop : Drag
            The Drag object that was dropped onto; this will always be None
            since there are no drop targets.
        """
        global persistent
        if not drags:
            return
        drag = drags[0]
        persistent.sprt_colorize_xpos = drag.x
        persistent.sprt_colorize_ypos = drag.y

    def save_recolor_info(picker):
        """Save the current information on the provided tag."""
        global persistent, num_shades, thresholds

        who = persistent.sprt_who

        kwargs = dict(extra=persistent.sprt_extra, num=num_shades,
            rgb=persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who))
        args = None

        who_key = get_image(who)
        if who_key == "image_not_found":
            return

        if persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who):
            if picker is not None:
                save_current_rgb_channel(picker)
            kwargs['Red'] = persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who, dict()).get("Red", [])
            kwargs['Green'] = persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who, dict()).get("Green", [])
            kwargs['Blue'] = persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who, dict()).get("Blue", [])
            args = persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who, dict()).get("Gray", [])
        if not args:
            if picker is None:
                args = persistent.sprt_color_dict.get(who_key, ((), dict()))[0]
                if args:
                    args = args[:MAX_COLORIZE_COLORS]
            if not args:
                if picker is None:
                    args = ["#fff", "#888", "#000"] + ["#000"]*(MAX_COLORIZE_COLORS-3)
                else:
                    args = [picker.get_color(i).hexcode for i in range(MAX_COLORIZE_COLORS)]
            args = list(args)
            args += list(thresholds)
            if (picker is None and persistent.sprt_color_dict.get(who_key)
                    and len(persistent.sprt_color_dict[who_key][0][:MAX_COLORIZE_COLORS]) > MAX_COLORIZE_COLORS*2):
                args.append(persistent.sprt_color_dict[who_key][0][-1])
            else:
                gray = persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who, dict()).get("Gray", [])
                if len(gray) > MAX_COLORIZE_COLORS*2:
                    args.append(gray[-1])
                else:
                    args.append(num_shades)
        args = tuple(args)

        persistent.sprt_color_dict[who_key] = (args, kwargs)
        return

    def fetch_recolor_info(who, picker, mb):
        """Apply the saved info for the provided tag."""
        global persistent, thresholds, num_shades

        args, kwargs = persistent.sprt_color_dict.get(who, ((), {}))
        if not args or not kwargs:
            return # Nothing to set up

        if kwargs.get('rgb', False):
            persistent.sprt_rgb_channel = "Gray"
            persistent.sprt_rgb_saved_colors.get(who, dict())["Red"] = kwargs.get('Red', [])
            persistent.sprt_rgb_saved_colors.get(who, dict())["Green"] = kwargs.get('Green', [])
            persistent.sprt_rgb_saved_colors.get(who, dict())["Blue"] = kwargs.get('Blue', [])
            if len(args) > MAX_COLORIZE_COLORS*2:
                change_num_shades(args[-1], mb)
            else:
                change_num_shades(kwargs.get('num', 3), mb)
            for i in range(MAX_COLORIZE_COLORS):
                picker.set_saved_color(i, args[i])
        else:
            for i in range(MAX_COLORIZE_COLORS):
                picker.set_saved_color(i, args[i])
            change_num_shades(kwargs.get('num', 3), mb)
        persistent.sprt_extra = kwargs.get('extra', "")
        thresholds = args[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2]

        picker.swap_to_saved_color(0)
        renpy.run(SetScreenVariable("current_color", 0))
        set_mb_values(mb)
        return

    def record_swatch_state(picker):
        """
        Record the current state of the swatches.
        """
        global num_shades, redo_list, undo_list, undo_history
        global redo_history, current_swatch_state
        ## Clear the redo lists
        redo_list.clear()
        redo_history.clear()

        ## Save the last current state
        if not current_swatch_state:
            return
        save_undo_info("color", current_swatch_state)
        ## Put together all the saved colours
        sd = dict()
        if not persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False):
            ## RGB not on; gray channel only
            sd["Gray"] = [picker.get_color(i).hexcode for i in range(MAX_COLORIZE_COLORS)]
        else:
            ## RGB on; record all channels
            for col in ("Red", "Green", "Blue", "Gray"):
                try:
                    sd[col] = persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][:MAX_COLORIZE_COLORS]
                except KeyError:
                    ## Reset this channel to the default
                    reset_rgb_channel(picker, col, None, save_state=False)
                    sd[col] = persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][:MAX_COLORIZE_COLORS]
                if len(persistent.sprt_rgb_saved_colors[persistent.sprt_who][col]) > MAX_COLORIZE_COLORS*2:
                    sd[col].append(persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][-1])
        current_swatch_state = sd
        save_recolor_info(picker)

    def record_threshold_state():
        """
        Record the current state of the thresholds.
        """
        global thresholds, redo_list, undo_list, undo_history, redo_history
        global current_threshold_state
        ## Clear the redo lists
        redo_list.clear()
        redo_history.clear()
        ## Save the last current state
        if not current_threshold_state:
            return
        save_undo_info("thresh", current_threshold_state)

        td = dict()
        if not persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False):
            ## RGB not on; gray channel only
            td["Gray"] = list(thresholds)
        else:
            ## RGB on; record all channels
            for col in ("Red", "Green", "Blue", "Gray"):
                td[col] = persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2]

        current_threshold_state = td
        save_recolor_info(None)
        renpy.restart_interaction()

    def save_undo_info(name, info):
        global undo_history, undo_list
        undo_list.append(name)
        undo_history.append(info)
        if len(undo_list) > MAX_UNDO_REDO:
            undo_list.pop(0)
            undo_history.pop(0)

    def set_up_initial_state(picker, clear_lists=True):
        """
        Set up the initial state for the undo/redo list.
        """
        global current_swatch_state, current_threshold_state, num_shades
        global redo_list, undo_list, redo_history, undo_history
        ## Save the initial state
        sd = dict()
        td = dict()
        if not persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False):
            ## RGB not on; gray channel only
            sd["Gray"] = [picker.get_color(i).hexcode for i in range(MAX_COLORIZE_COLORS)]
            td["Gray"] = list(thresholds)
        else:
            ## RGB on; record all channels
            for col in ("Red", "Green", "Blue", "Gray"):
                try:
                    sd[col] = persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][:MAX_COLORIZE_COLORS]
                    td[col] = persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2]
                except KeyError:
                    ## Reset this channel to the default
                    reset_rgb_channel(picker, col, None, save_state=False)
                    sd[col] = persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][:MAX_COLORIZE_COLORS]
                    td[col] = persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2]
                if len(persistent.sprt_rgb_saved_colors[persistent.sprt_who][col]) > MAX_COLORIZE_COLORS*2:
                    sd[col].append(persistent.sprt_rgb_saved_colors[persistent.sprt_who][col][-1])

        current_swatch_state = sd
        current_threshold_state = td
        if clear_lists:
            redo_list.clear()
            undo_list.clear()
            redo_history.clear()
            undo_history.clear()

    def set_up_rd_thresholds(mb, td, who):
        """
        Set up the thresholds based on the provided threshold dictionary.
        """
        global thresholds, persistent, num_shades
        ## Actually update the thresholds
        if not persistent.sprt_rgb_recolorize_on.get(who, False):
            ## RGB not on; gray channel only
            thresholds = list(td["Gray"])
        else:
            ## RGB on; update the thresholds with the current channel
            thresholds = list(td[persistent.sprt_rgb_channel])

            ## And save the other channels
            for chan in [x for x in ["Red", "Green", "Blue", "Gray"] if x != persistent.sprt_rgb_channel]:
                old_col = persistent.sprt_rgb_saved_colors[who][chan][:MAX_COLORIZE_COLORS]
                old_num = num_shades
                if len(persistent.sprt_rgb_saved_colors[who][chan]) > MAX_COLORIZE_COLORS*2:
                    old_num = persistent.sprt_rgb_saved_colors[who][chan][-1]
                persistent.sprt_rgb_saved_colors[who][chan] = old_col + td[chan]
                persistent.sprt_rgb_saved_colors[who][chan].append(old_num)

        set_mb_values(mb)

    def set_up_rd_colors(picker, ts, who):
        """
        Set up the colours based on the provided colour dictionary.
        """
        global persistent
        ## Actually update the colours
        if not persistent.sprt_rgb_recolorize_on.get(who, False):
            ## RGB not on; gray channel only
            for i, col in enumerate(ts["Gray"][:MAX_COLORIZE_COLORS]):
                picker.set_saved_color(i, col)
        else:
            ## RGB on; update the picker with the current channel
            for i, col in enumerate(ts[persistent.sprt_rgb_channel][:MAX_COLORIZE_COLORS]):
                picker.set_saved_color(i, col)
            ## And save the other channels
            for chan in [x for x in ["Red", "Green", "Blue", "Gray"] if x != persistent.sprt_rgb_channel]:
                old_thresh = persistent.sprt_rgb_saved_colors[who][chan][MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2]
                persistent.sprt_rgb_saved_colors[who][chan] = list(ts[chan][:MAX_COLORIZE_COLORS])
                persistent.sprt_rgb_saved_colors[who][chan] += old_thresh
                if len(ts[chan]) > MAX_COLORIZE_COLORS:
                    persistent.sprt_rgb_saved_colors[who][chan].append(ts[chan][-1])

    def undo(picker, mb):
        """
        Undoes the most recent action.
        """
        global undo_list, redo_list, redo_history, undo_history, undo_swatch
        global undo_thresh, current_swatch_state, current_threshold_state
        global thresholds, num_shades
        if not undo_list:
            ## Nothing that can be undone
            return

        ## Get the state we're undoing to
        last_action = undo_list.pop()
        lsc = picker.last_saved_color if picker.last_saved_color < num_shades else 0

        if last_action == "color":
            ## Save the current colours to the redo list
            redo_list.append(last_action)
            redo_history.append(current_swatch_state)
            ## Pop the previous colours to put into the current swatch state
            current_swatch_state = undo_history.pop()
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
        elif last_action == "thresh":
            ## Save the current thresholds to the redo list
            redo_list.append(last_action)
            redo_history.append(current_threshold_state)
            ## Pop the previous thresholds to put into the current threshold state
            current_threshold_state = undo_history.pop()
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        elif last_action.startswith("add"):
            ## Added a swatch; now we have to remove it
            redo_list.append(last_action)
            channel = last_action.split(' ')[-1]
            redo_history.append((current_swatch_state, current_threshold_state))
            colors, thresh = undo_history.pop()
            if channel == persistent.sprt_rgb_channel:
                ## Change it right now
                change_num_shades(num_shades-1, mb)
                lsc = picker.last_saved_color if picker.last_saved_color < num_shades else 0
            current_swatch_state = colors
            current_threshold_state = thresh
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        elif last_action.startswith("remove"):
            ## Removed a swatch; add it back in
            redo_list.append(last_action)
            channel = last_action.split(' ')[-1]
            redo_history.append((current_swatch_state, current_threshold_state))
            colors, thresh = undo_history.pop()
            if channel == persistent.sprt_rgb_channel:
                change_num_shades(num_shades+1, mb)
            current_swatch_state = colors
            current_threshold_state = thresh
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        elif last_action.startswith("refresh"):
            ## Refreshed the swatches; undo it
            redo_list.append(last_action)
            channel, og_num, refreshed_num = last_action.split(' ')[1:]
            redo_history.append((current_swatch_state, current_threshold_state))
            colors, thresh = undo_history.pop()
            if channel == persistent.sprt_rgb_channel:
                ## Update the mb right now
                change_num_shades(int(og_num), mb)
            ## TODO?
            current_swatch_state = colors
            current_threshold_state = thresh
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        picker.swap_to_saved_color(lsc)
        renpy.run(SetScreenVariable("current_color", lsc))
        save_recolor_info(picker)

    def redo(picker, mb):
        """
        Redoes the most recent action.
        """
        global undo_list, redo_list, redo_history, undo_history, undo_swatch
        global current_swatch_state, current_threshold_state
        global thresholds, num_shades
        if not redo_list:
            ## Nothing that can be redone
            return

        lsc = picker.last_saved_color if picker.last_saved_color < num_shades else 0

        ## Get the state we're redoing to
        last_action = redo_list.pop()
        if last_action == "color":
            ## Save the current colours to the undo list
            undo_list.append(last_action)
            undo_history.append(current_swatch_state)
            ## Pop the previous colours to put into the current swatch state
            current_swatch_state = redo_history.pop()
            ## Actually update the colours
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
        elif last_action == "thresh":
            ## Save the current thresholds to the undo list
            undo_list.append(last_action)
            undo_history.append(current_threshold_state)
            ## Pop the previous thresholds to put into the current threshold state
            current_threshold_state = redo_history.pop()
            ## Actually update the thresholds
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        elif last_action.startswith("add"):
            channel = last_action.split(' ')[-1]
            ## Re-add the swatch
            undo_list.append(last_action)
            undo_history.append((current_swatch_state, current_threshold_state))
            colors, thresh = redo_history.pop()
            if channel == persistent.sprt_rgb_channel:
                change_num_shades(num_shades+1, mb)
            current_swatch_state = colors
            current_threshold_state = thresh
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        elif last_action.startswith("remove"):
            channel = last_action.split(' ')[-1]
            ## Re-remove the swatch
            undo_list.append(last_action)
            undo_history.append((current_swatch_state, current_threshold_state))
            colors, thresh = redo_history.pop()
            if channel == persistent.sprt_rgb_channel:
                change_num_shades(num_shades-1, mb)
                lsc = picker.last_saved_color if picker.last_saved_color < num_shades else 0
            current_swatch_state = colors
            current_threshold_state = thresh
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        elif last_action.startswith("refresh"):
            channel, og_num, refreshed_num = last_action.split(' ')[1:]
            ## Re-refresh the swatches
            undo_list.append(last_action)
            undo_history.append((current_swatch_state, current_threshold_state))
            colors, thresh = redo_history.pop()
            if channel == persistent.sprt_rgb_channel:
                ## Update the mb right now
                change_num_shades(int(refreshed_num), mb)
            current_swatch_state = colors
            current_threshold_state = thresh
            set_up_rd_colors(picker, current_swatch_state, persistent.sprt_who)
            set_up_rd_thresholds(mb, current_threshold_state, persistent.sprt_who)
        picker.swap_to_saved_color(lsc)
        renpy.run(SetScreenVariable("current_color", lsc))
        save_recolor_info(picker)

    ## BAR FUNCTIONS ###########################################################

    def change_num_shades(new_num, mb):
        """Update the number of shades, and the multibar."""
        global num_shades
        num_shades = new_num
        try:
            mb.refresh_thumbs(num_shades)
        except Exception as e:
            return ## Likely they do not have MultiBar

    def set_mb_values(mb, return_values=False):
        """Set the multibar values (if possible)."""
        global thresholds, num_shades
        ## First, check if the number of thumbs needs to be updated
        try:
            old_thresholds = list(thresholds)
            mb.refresh_thumbs(num_shades)
            thresholds = old_thresholds
        except Exception as e:
            pass ## Likely they do not have MultiBar, or it does not exist yet

        new_thresh = [ ]
        for i in range(num_shades):
            if i == 0:
                new_thresh.append(255-thresholds[i])
            else:
                new_thresh.append(thresholds[i-1]-thresholds[i])

        new_values = new_thresh[:num_shades] + [255-sum(new_thresh[:num_shades])]
        if return_values:
            return new_values
        try:
            mb.set_current_values(new_values)
            renpy.redraw(mb, 0)
        except Exception as e:
            pass

    def copy_thresholds():
        global thresholds, num_shades
        ret = ''
        ret += ", ".join([str(x) for x in thresholds[:num_shades]])
        ret = "[{}]".format(ret)
        copy_to_clipboard(ret)

    def reset_thresholds(mb):
        """Reset the thresholds to their defaults."""
        global thresholds, num_shades
        div = 255.0 / max(num_shades-1, 1)
        thresholds = [round(div*i) for i in range(num_shades)]
        thresholds.reverse() ## Thresholds go from 255 (lightest) to 0 (darkest)
        if num_shades < MAX_COLORIZE_COLORS:
            thresholds += [0]*(MAX_COLORIZE_COLORS-num_shades)
        set_mb_values(mb)
        record_threshold_state()

    def update_thresholds(mb, old, removing=None, adding=None):
        """
        Update the thresholds to reflect the addition/removal of a swatch.
        """
        global thresholds, num_shades
        if removing is not None:
            ## Getting rid of a swatch
            removed = old.pop(removing)
            old.append(0)
            thresholds = old
        elif adding is not None:
            ## Add it in with a threshold of 0 so it doesn't interfere
            ## with the other swatches
            thresholds = old[:adding] + [0]*(MAX_COLORIZE_COLORS-num_shades+1)
        set_mb_values(mb)

    def update_shader_values(values):
        """
        Updates the appropriate variables based on the multibar values. Used
        as a changed callback by the multibar.
        """
        global thresholds, num_shades
        thresholds = [0]*MAX_COLORIZE_COLORS
        for i in range(min(MAX_COLORIZE_COLORS, len(values))):
            thresholds[i] = sum(values[i:]) - values[i]

    class ThresholdValue(DictValue):
        """
        A subclass of DictValue which keeps the thresholds within appropriate
        bounds.
        """
        def changed(self, value):
            global thresholds
            rv = super(ThresholdValue, self).changed(value)
            ## The key is our threshold value. It has to be >= than the key
            ## before it and <= than the key after it.
            ## Check the keys after (should have lower numbers)
            refresh = False
            value = self.dict[self.key]
            for i in range(self.key+1, MAX_COLORIZE_COLORS):
                if value < thresholds[i]:
                    thresholds[i] = value
                    refresh = True
            ## Check the keys before (should have higher numbers)
            for i in range(self.key-1, -1, -1):
                if value > thresholds[i]:
                    thresholds[i] = value
                    refresh = True
            if refresh:
                renpy.restart_interaction()

    ## INPUT VALIDATION FUNCTIONS ##############################################

    def check_recolor_who_c(dev_who, picker, mb):
        """
        A callback used by the input for persistent.sprt_who which confirms
        if the input is a valid image name or not, and applies the
        recoloring system to it if so.
        """
        global persistent, last_valid_image

        if not dev_who:
            return "image_not_found"

        last_last_valid_image = last_valid_image

        def set_up_image_colorize(img, tg, picker, mb):
            renpy.run([Function(retrieve_xyinitial, tg),
                Function(fetch_recolor_info, tg, picker, mb),
                Function(switch_rgb_channels, picker, "Gray", mb),
                SetScreenVariable("recolored_img",
                    DynamicDisplayable(pick_multi_color,
                    img=get_image(img, save_last_image=True), picker=picker))])

        tag, attrs = get_tag_attrs(dev_who, '')
        attrs = ' '.join(attrs)
        img = "{} {}".format(tag, attrs).strip()

        result = renpy.can_show(img)

        if result is not None:
            last_valid_image = ' '.join(result)
            set_up_image_colorize(last_valid_image, dev_who, picker, mb)
            if last_last_valid_image != last_valid_image:
                set_up_initial_state(picker)
            return last_valid_image

        result = renpy.get_registered_image(dev_who)
        if result is not None:
            last_valid_image = dev_who
            set_up_image_colorize(last_valid_image, dev_who, picker, mb)
            if last_last_valid_image != last_valid_image:
                set_up_initial_state(picker)
            return img

        if renpy.loadable(dev_who):
            last_valid_image = dev_who
            set_up_image_colorize(last_valid_image, dev_who, picker, mb)
            if last_last_valid_image != last_valid_image:
                set_up_initial_state(picker)
            return dev_who
        elif renpy.loadable("images/{}".format(dev_who)):
            dh = "images/{}".format(dev_who)
            set_up_image_colorize(last_valid_image, dh, picker, mb)
            if last_last_valid_image != last_valid_image:
                set_up_initial_state(picker)
            return dh

        if last_valid_image is not None:
            set_up_image_colorize(last_valid_image, None, picker, mb)
            if last_last_valid_image != last_valid_image:
                set_up_initial_state(picker)
            return last_valid_image
        return "image_not_found"

    check_recolor_who = renpy.curry(check_recolor_who_c)

    def check_hex_c(hexcode, picker):
        """
        A function which checks if the provided hexcode is valid, and if so,
        saves it in the picker.
        """
        try:
            x = Color("#" + hexcode)
            picker.set_color(x)
            picker.save_color(picker.last_saved_color)
            record_swatch_state(picker)
        except Exception as e:
            pass

    check_hex = renpy.curry(check_hex_c)

    def check_extra(s):
        """
        Ensure the provided extra image is valid. If not, return the empty
        string.
        """
        if renpy.get_registered_image(s) is not None:
            return s
        elif renpy.loadable(s):
            return s
        elif renpy.loadable("images/{}".format(s)):
            return "images/{}".format(s)
        else:
            return ""

    def update_hex(picker):
        """
        Ensure that the displayed hexcode matches the picker's, sans the
        leading #.
        """
        global hexcode
        hexcode = picker.color.hexcode[1:]

    def parse_rgbc_c(txt, picker, mb):
        """
        Turn a line like RGBColorize(["#fff", "#000"]) into the actual
        colours and thresholds for this image.
        """
        global persistent, num_shades, thresholds, rgbc_obj
        from re import sub, findall
        rgbc = dict()
        try:
            ## First: get rid of all spaces
            txt = sub(r"\s", "", txt)
            ## Get rid of "RGBColorize(" at the start and the ")" at the end
            txt = sub(r"RGBColorize\(|\)$", "", txt)

            ## Does it have kwargs or just args?
            m = findall("([a-zA-Z_0-9]+)=\[([^\]]+)]", txt)
            if m:
                for kw, args in m:
                    args = args.split(',')
                    if "'" in args[0] or '"' in args[0]:
                        args = [sub("['\"]", "", x) for x in args]
                    else:
                        args = [int(x) for x in args]
                    rgbc[kw] = args
            txt = sub("([a-zA-Z_0-9]+)=\[([^\]]+)]", "", txt)

            m = findall("\[([^\]]+)]", txt)
            for args, kw in zip(m, ["gray", "gray_thresh", "red", "red_thresh",
                    "green", "green_thresh", "blue", "blue_thresh"]):
                args = args.split(',')
                if "'" in args[0] or '"' in args[0]:
                    args = [sub("['\"]", "", x) for x in args]
                else:
                    args = [int(x) for x in args]
                rgbc[kw] = args
        except Exception as e:
            print("ERROR: Could not parse", txt, "as RGBColorize arguments.")

        try:
            final = RGBColorize(**rgbc)
        except Exception as e:
            print("ERROR: Could not create RGBColorize object from", rgbc)
            return
        rgbc_obj = final

    parse_rgbc = renpy.curry(parse_rgbc_c)

    def apply_rgbc(rgbc, picker, mb):
        """
        Apply the provided RGBColorize object to the picker and multibar.
        """
        global num_shades, thresholds, persistent
        who = persistent.sprt_who
        if not rgbc.rgb:
            ## Turn off RGB if it's on
            if persistent.sprt_rgb_recolorize_on.get(who, False):
                toggle_rgb_recolorize(picker, mb)
        elif not persistent.sprt_rgb_recolorize_on.get(who, False):
            ## Turn on RGB if it's off
            toggle_rgb_recolorize(picker, mb)

        if rgbc.rgb:
            for chan, lst, thr in zip(["Gray", "Red", "Green", "Blue"],
                    [rgbc.gray, rgbc.red, rgbc.green, rgbc.blue],
                    [rgbc.gray_thresh, rgbc.red_thresh, rgbc.green_thresh,
                        rgbc.blue_thresh]):
                persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who,
                    dict())[chan] = lst + [round(x*255) for x in thr]
        else:
            ## Gray only
            for i, col in enumerate(rgbc.gray):
                picker.set_saved_color(i, col)

        ## Set to default channel
        persistent.sprt_rgb_channel = "Gray"
        ## Set the num_shades
        change_num_shades(rgbc.num_shades, mb)
        ## Update the picker
        for i, col in enumerate(rgbc.gray):
            picker.set_saved_color(i, col)
        ## Update the thresholds
        thresholds = [round(x*255) for x in rgbc.gray_thresh]
        set_mb_values(mb)

        picker.swap_to_saved_color(0)
        renpy.run(SetScreenVariable('current_color', 0))
        set_up_initial_state(picker)
        save_recolor_info(picker)

    def check_input(specific=False):
        """
        Return whether any or a specific input value is active.
        """
        val, editable = renpy.get_editable_input_value()
        if not specific:
            if val is None:
                return False
            return editable
        else:
            if val is not specific:
                return False
            return editable

    def check_threshold_input_c(values, mb):
        if not values:
            return
        ## See if we can parse it into a list of ints
        values = values.strip()
        while values.endswith(','):
            values = values[:-1]
        try:
            if ',' in values:
                values = values.split(',')
            elif ' ' in values:
                values = values.split(' ')
            else:
                values = [values]
            values = [int(x.strip()) for x in values]
        except Exception as e:
            print("Could not turn thresholds into a list of ints.")
            return
        ## Just nerf any values that are higher than the last one
        new_values = list(values)
        values = [ ]
        for v in new_values:
            if not values:
                values.append(v)
                continue
            values.append(min(v, values[-1]))

        ## If any value is higher than 255 or lower than 0, abort
        if any([x > 255 or x < 0 for x in values]):
            print("Thresholds must be between 0 and 255.")
            return
        ## Otherwise, these are valid thresholds. Set it up.
        global thresholds, num_shades
        thresholds = values[:num_shades] + [0]*(MAX_COLORIZE_COLORS-num_shades)
        if len(thresholds) < MAX_COLORIZE_COLORS:
            thresholds += [0]*(MAX_COLORIZE_COLORS-len(thresholds))
        set_mb_values(mb)
        return

    check_threshold_input = renpy.curry(check_threshold_input_c)

    def within_range(comparison, num, decimal_points=5):
        """
        Return whether the provided number is within the range of the
        comparison number, with the provided number of decimal points.
        """
        thresh_num = 1/(10**decimal_points)
        return abs(comparison-num) < thresh_num

    def is_valid_for_colorize(who):
        """
        Return True if the provided image is valid.
        """
        if not who:
            return False

        tag, attrs = get_tag_attrs(who, tuple())
        attrs = ' '.join(attrs)
        img = "{} {}".format(tag, attrs).strip()

        result = renpy.can_show(img)

        if result is not None:
            return True
        elif renpy.loadable(who):
            return True
        elif renpy.loadable("images/{}".format(who)):
            return True
        return False

    ## DYNAMIC DISPLAYABLES ####################################################

    def pick_multi_color(st, at, img, picker):
        """
        A DynamicDisplayable function to show a colorized image based on a
        series of colour picker colours and thresholds.
        """
        global thresholds, num_shades

        colors = [picker.get_color(i) for i in range(MAX_COLORIZE_COLORS)]
        thresh = [thresholds[i]/255.0 for i in range(MAX_COLORIZE_COLORS)]

        save_current_rgb_channel(picker)
        if not persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False):
            tf = RGBColorize(colors[:num_shades], thresh[:num_shades],
                blend=persistent.sprt_blend_gradient,
                name=persistent.sprt_who).transform
        else:
            ## Recolour based on RGB channels
            if len(persistent.sprt_rgb_saved_colors[persistent.sprt_who].keys()) < 4:
                ## No saved colours; use the defaults
                set_up_all_rgb_channels(picker)
            red_c, red_t = persistent.sprt_rgb_saved_colors[persistent.sprt_who]['Red'][:MAX_COLORIZE_COLORS], persistent.sprt_rgb_saved_colors[persistent.sprt_who]['Red'][MAX_COLORIZE_COLORS:]
            green_c, green_t = persistent.sprt_rgb_saved_colors[persistent.sprt_who]['Green'][:MAX_COLORIZE_COLORS], persistent.sprt_rgb_saved_colors[persistent.sprt_who]['Green'][MAX_COLORIZE_COLORS:]
            blue_c, blue_t = persistent.sprt_rgb_saved_colors[persistent.sprt_who]['Blue'][:MAX_COLORIZE_COLORS], persistent.sprt_rgb_saved_colors[persistent.sprt_who]['Blue'][MAX_COLORIZE_COLORS:]
            colors, thresh = persistent.sprt_rgb_saved_colors[persistent.sprt_who]["Gray"][:MAX_COLORIZE_COLORS], persistent.sprt_rgb_saved_colors[persistent.sprt_who]["Gray"][MAX_COLORIZE_COLORS:]

            if len(red_t) > MAX_COLORIZE_COLORS:
                red_num = red_t[-1]
                ret_t = red_t[:-1]
            else:
                red_num = num_shades
            if len(green_t) > MAX_COLORIZE_COLORS:
                green_num = green_t[-1]
                green_t = green_t[:-1]
            else:
                green_num = num_shades
            if len(blue_t) > MAX_COLORIZE_COLORS:
                blue_num = blue_t[-1]
                blue_t = blue_t[:-1]
            else:
                blue_num = num_shades
            if len(thresh) > MAX_COLORIZE_COLORS:
                num = thresh[-1]
                thresh = thresh[:-1]
            else:
                num = num_shades

            tf = RGBColorize(colors[:num], thresh[:num],
                red_c[:red_num], red_t[:red_num],
                green_c[:green_num], green_t[:green_num],
                blue_c[:blue_num], blue_t[:blue_num],
                blend=persistent.sprt_blend_gradient,
                name=persistent.sprt_who).transform
        return At(img, tf), 0.05

    def get_gradient_bar(st, at, picker, left, right):
        """
        A DynamicDisplayable which returns a gradient based on the provided
        left and right numbers and the picker.
        """
        global num_shades
        ## min ensures we don't show colours beyond the number of swatches
        ## currently being used.
        return At("#fff", renpy.store.multicolor_image_transform(
            picker.get_color(min(left, num_shades-1)),
            picker.get_color(min(right, num_shades-1)))), 0.1

    def static_gradient_bar(st, at, picker):
        """
        A DynamicDisplayable which returns a gradient bar based on the
        provided picker.
        """
        global thresholds, num_shades
        picker_colors = [picker.get_color(i) for i in range(num_shades)]
        return At("#fff", renpy.store.multicolor_image_transform(*picker_colors)), 0.1

    def display_hexcode(st, at, picker):
        """
        A DynamicDisplayable that displays the picker's current colour code
        in real-time.
        """
        return Fixed(Text(picker.color.hexcode, style='sprt_text', color="#000"),
            xsize=SWATCH_WIDTH, yfit=True), 0.05

    def current_picker_color(st, at, picker, xsize=100, ysize=100):
        """
        A DynamicDisplayable function to update the colour picker swatch.

        Parameters:
        -----------
        picker : ColorPicker
            The picker this swatch is made from.
        xsize : int
            The width of the swatch.
        ysize : int
            The height of the swatch.
        """
        return Transform(picker.color, xysize=(xsize, ysize)), 0.05

    ## SWATCH FUNCTIONS ########################################################

    def remove_swatch(picker, num, mb):
        """
        Remove the numbered swatch from the column of swatches.
        """
        global persistent, num_shades, undo_list, undo_history, thresholds
        global current_swatch_state, current_threshold_state
        old = list(thresholds)

        change_num_shades(num_shades-1, mb)
        lsc = picker.last_saved_color if picker.last_saved_color < num_shades else 0
        ## Shuffle the swatches down
        for i in range(num, num_shades):
            picker.set_saved_color(i, picker.get_color(i+1))

        update_thresholds(mb, old, removing=num)
        save_undo_info("remove " + persistent.sprt_rgb_channel,
            (current_swatch_state, current_threshold_state))
        set_up_initial_state(picker, clear_lists=False)
        save_recolor_info(picker)
        ## Swap to the first colour for safety, since they might've removed
        ## the current swatch (and they always have to have one swatch).
        picker.swap_to_saved_color(lsc)
        renpy.run(SetScreenVariable("current_color", lsc))

    def add_swatch(picker, mb):
        """
        Add another swatch to the column of swatches.
        """
        global persistent, num_shades, undo_list, undo_history, thresholds
        global current_swatch_state, current_threshold_state

        old = list(thresholds)

        change_num_shades(num_shades+1, mb)
        ## Make the new swatch the active swatch
        picker.swap_to_saved_color(num_shades-1)
        update_thresholds(mb, old, adding=num_shades-1)
        ## Record that a swatch was added
        save_undo_info("add " + persistent.sprt_rgb_channel,
            (current_swatch_state, current_threshold_state))
        set_up_initial_state(picker, clear_lists=False)
        save_recolor_info(picker)

    def swap_swatch(picker, num, mb):
        """
        Swap two swatches with each other.
        """
        ## Swap this number with the one beneath it
        top_color = picker.get_color(num)
        bottom_color = picker.get_color(num+1)
        picker.set_saved_color(num, bottom_color)
        picker.set_saved_color(num+1, top_color)
        picker.swap_to_saved_color(0)
        save_recolor_info(picker)
        record_swatch_state(picker)

    ## RGB FUNCTIONS ###########################################################

    def set_up_all_rgb_channels(picker):
        """
        Set up all RGB channels for the provided picker.
        """
        global persistent
        for chan in ("Red", "Blue", "Green"):
            reset_rgb_channel(picker, chan, None)

    def toggle_rgb_recolorize(picker, mb):
        """
        Toggle the RGB recolorize mode.
        """
        global persistent
        save_xyinitial()
        if persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who):
            switch_rgb_channels(picker, "Gray", mb)
            persistent.sprt_rgb_recolorize_on[persistent.sprt_who] = False
        else:
            ## Save the defaults
            if not persistent.sprt_rgb_saved_colors.get(persistent.sprt_who):
                save_current_rgb_channel(picker)
                ## Set all RGB channels to the current defaults
                set_up_all_rgb_channels(picker)
                ## Switch to the gray channel
                switch_rgb_channels(picker, "Gray", mb)
            else:
                save_current_rgb_channel(picker)
            persistent.sprt_rgb_recolorize_on[persistent.sprt_who] = True

        picker.swap_to_saved_color(0)
        ## Refresh the image
        check_recolor_who_c(persistent.sprt_who, picker, mb)

    def save_current_rgb_channel(picker):
        """
        Save the current RGB channel's colours and thresholds.
        """
        global persistent, thresholds, num_shades
        if not is_valid_for_colorize(persistent.sprt_who):
            return
        persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who,
                dict())[persistent.sprt_rgb_channel] = ([
            picker.get_color(i).hexcode for i in range(MAX_COLORIZE_COLORS)]
            + list(thresholds) + [num_shades])

    def switch_rgb_channels(picker, channel, mb):
        """
        Switch the RGB channel being edited.
        """
        global persistent, thresholds, num_shades
        if not is_valid_for_colorize(persistent.sprt_who):
            return
        ## Save the current colours
        save_current_rgb_channel(picker)
        persistent.sprt_rgb_channel = channel
        ## Set up the channel with any saved information
        info = persistent.sprt_rgb_saved_colors[persistent.sprt_who].get(channel)
        if info:
            for i, col in enumerate(info[:MAX_COLORIZE_COLORS]):
                picker.set_saved_color(i, col)
            if len(info) > MAX_COLORIZE_COLORS*2:
                change_num_shades(info[-1], mb)
            thresholds = info[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2]
            set_mb_values(mb)
        else:
            reset_thresholds(mb)
        ## Swap to the first swatch for safety
        picker.swap_to_saved_color(0)
        renpy.run(SetScreenVariable("current_color", 0))
        ## Save this as the current recoloured state of the image
        save_recolor_info(picker)

    def reset_rgb_channel(picker, channel, mb, save_state=True):
        """
        Set this channel to the default channel's colours and thresholds.
        """
        global persistent, thresholds, num_shades
        colors = [ ]
        original_num = num_shades
        default_colors = persistent.sprt_rgb_saved_colors.setdefault(
                persistent.sprt_who, dict()).get("Gray")
        if not default_colors:
            default_colors = [ picker.get_color(i).hexcode for i in range(MAX_COLORIZE_COLORS)]
            default_thresholds = list(thresholds)
            default_num = num_shades
            persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who,
                dict())["Gray"] = default_colors + default_thresholds + [num_shades]
        else:
            if len(default_colors) > MAX_COLORIZE_COLORS*2:
                default_num = default_colors[-1]
            else:
                default_num = num_shades
            change_num_shades(default_num, mb)
            default_thresholds = default_colors[MAX_COLORIZE_COLORS:MAX_COLORIZE_COLORS*2]
            default_colors = default_colors[:MAX_COLORIZE_COLORS]

        for i, col in enumerate(default_colors):
            picker.set_saved_color(i, col)
            colors.append(col)
        thresholds = list(default_thresholds)
        persistent.sprt_rgb_saved_colors.setdefault(persistent.sprt_who,
                dict())[channel] = colors + thresholds + [default_num]

        if save_state:
            set_mb_values(mb)
            picker.swap_to_saved_color(0)
            renpy.run(SetScreenVariable("current_color", 0))
            save_undo_info("refresh {} {} {}".format(persistent.sprt_rgb_channel,
                original_num, default_num),
                (current_swatch_state, current_threshold_state))
            set_up_initial_state(picker, clear_lists=False)
            save_recolor_info(picker)

################################################################################
## SCREENS
################################################################################
screen colorizing_tool():
    tag menu

    ## The colour picker
    default picker = ColorPicker(sprt.PICKER_SIZE, sprt.PICKER_SIZE,
        sprt.fetch_initial_colors(persistent.sprt_who)[0],
        saved_colors=sprt.fetch_initial_colors(persistent.sprt_who),
        last_saved_color=0, mouseup_callback=sprt.record_swatch_state)

    ## The multibar (if it was possible to make)
    default mb = sprt.make_multibar(picker)

    ## The input values for the character name and extra images
    default sprt_who_input = SpecialInputValue(persistent, 'sprt_who',
        set_callback=sprt.check_recolor_who(picker=picker, mb=mb),
        enter_callback=sprt.save_xyinitial)
    default extra_input = SpecialInputValue(persistent, 'sprt_extra',
        set_callback=sprt.check_extra)

    ## The dynamic displayable with the recoloured image
    default recolored_img = DynamicDisplayable(sprt.pick_multi_color,
        img=sprt.get_image(persistent.sprt_who, True), picker=picker)

    ## Information on the current tab and colour
    default current_color = 0
    default current_tab = 0
    ## Whether the user is entering in an RGBColorize object
    default enter_rgb_colorize = False
    default rgbc_input = SpecialInputValue(sprt, 'rgbc_input',
        set_callback=sprt.parse_rgbc(picker=picker, mb=mb))

    on 'show' action [Function(sprt.set_up_initial_state, picker),
        If(not persistent.sprt_tutorial5_shown, Show("sprt_colorize_tutorial"))]
    on 'replace' action [Function(sprt.set_up_initial_state, picker),
        If(not persistent.sprt_tutorial5_shown, Show("sprt_colorize_tutorial"))]

    predict False

    add sprt.GRAY ## The background

    use sprt_add_colorize_comparison()

    ## The viewport for the recoloured image and any additional layers
    use sprt_viewport(False, True):
        use sprt_viewport_extras(recolored_img)

    ## The buttons at the top right for general tasks
    hbox:
        style_prefix 'sprt_copy'
        textbutton "⟲":
            sensitive sprt.undo_list
            keysym "ctrl_K_z"
            tooltip "|Undo the last threshold or colour change. (Ctrl+Z)"
            insensitive_background sprt.construct_frame("#888", "#000", sprt.PADDING)
            action Function(sprt.undo, picker, mb)
        textbutton "⟳":
            keysym "ctrl_K_y"
            tooltip "|Redo the last threshold or colour change. (Ctrl+Y)"
            sensitive sprt.redo_list
            insensitive_background sprt.construct_frame("#888", "#000", sprt.PADDING)
            action Function(sprt.redo, picker, mb)
        textbutton "Blend {}".format("on" if persistent.sprt_blend_gradient else "off"):
            keysym "ctrl_K_b"
            tooltip "|Toggle blending on and off. (Ctrl+B)\nMost of the final results should be with blending on, but toggling it off can help you identify how thresholds correspond with the colours you've chosen."
            action ToggleField(persistent, 'sprt_blend_gradient')
        textbutton "Save Colors":
            keysym "ctrl_K_s"
            tooltip "|Save the current colours in the colour picker to the swatch gallery. (Ctrl+S)"
            action If(not sprt.HAS_COLORIZE_EXTRAS,
                Notify("This feature is included in the Colorize Tool Extras addon!"),
                [SetField(sprt, 'swatch_text', ""),
                Show('sprt_saving_swatches_screen', picker=picker, mb=mb)])
        textbutton "Copy Colors":
            keysym "ctrl_K_c"
            tooltip "|Copy an RGBColorize with the information on the current tag to the clipboard. (Ctrl+C)"
            action Function(sprt.copy_colors_to_clipboard, picker)

    ## Darken the screen when the input is active
    if sprt.check_input(extra_input):
        add sprt.GRAY alpha 0.7
        dismiss action [sprt_who_input.Disable(),
            Function(sprt.save_recolor_info, picker),
            extra_input.Disable()]

    ## The main draggable frame with the colour picker and other tabs.
    drag:
        id 'text_attr_drag'
        draggable True drag_handle (0, 0, 1.0, sprt.SPACER*2)
        dragged sprt.record_colorize_drag_pos
        pos (persistent.sprt_colorize_xpos, persistent.sprt_colorize_ypos)
        frame:
            style_prefix 'sprt_drag'
            ymaximum config.screen_height-sprt.SPACER*3
            xsize sprt.PICKER_FRAME_SIZE
            has vbox
            spacing sprt.PADDING*2 xalign 0.5
            frame:
                style 'sprt_drag_label'
                text "(Drag to move)"
                ## The two tabs
                hbox:
                    textbutton "Color Picker":
                        action [Function(sprt.save_recolor_info, picker),
                            SetScreenVariable('current_tab', 0)]
                    textbutton "Swatches":
                        action [Function(sprt.save_recolor_info, picker),
                            If(sprt.HAS_COLORIZE_EXTRAS,
                                SetScreenVariable('current_tab', 1),
                                Notify("This feature is included in the Colorize Tool Extras addon!"),
                            )]
                    textbutton "Layers":
                        action [Function(sprt.save_recolor_info, picker),
                            If(sprt.HAS_COLORIZE_EXTRAS,
                                SetScreenVariable('current_tab', 2),
                                Notify("This feature is included in the Colorize Tool Extras addon!"),
                            )]

            if current_tab == 0:
                use sprt_recolor_tab1(picker, mb, current_color,
                    enter_rgb_colorize, rgbc_input)
            elif current_tab == 1:
                use sprt_recolor_tab2(picker, current_color, mb)
            else:
                use sprt_recolor_tab3(picker, mb, sprt_who_input, extra_input)

    ## Dim the background behind the input button when it's active
    if sprt.check_input(sprt_who_input):
        add sprt.GRAY alpha 0.7
        dismiss action [Function(sprt.save_recolor_info, picker),
            DisableAllInputValues()]

    ## The tag input
    vbox:
        xanchor 0.0 yanchor 0.0 spacing sprt.PADDING*2
        xpos sprt.MENU_SIZE+sprt.SPACER*2
        frame:
            style_prefix 'sprt_small'
            if sprt.check_input(extra_input):
                foreground Transform(sprt.GRAY, alpha=0.7)
            has hbox
            textbutton "Tag:" action [Function(sprt.save_recolor_info, picker),
                    CaptureFocus("tag_drop")]:
                tooltip "|Select previously saved tags in a dropdown."
            button:
                style_prefix 'sprt_input'
                key_events True
                tooltip "|Enter an image path or image tag to colorize."
                selected sprt.check_input(sprt_who_input)
                action [sprt_who_input.Toggle(),
                    Function(sprt.save_recolor_info, picker),
                    Function(sprt.save_xyinitial)]
                at transform:
                    crop (0.0, 0.0, 1.0, 1.0)
                input value sprt_who_input allow sprt.INPUT_ALLOW:
                    xalign 1.0 layout 'nobreak' text_align 1.0 copypaste True
            textbutton "Clear":
                tooltip "|Clear the tag input."
                sensitive persistent.sprt_who
                action [If(persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who),
                            Function(sprt.toggle_rgb_recolorize, picker, mb)),
                        SetField(persistent, "sprt_who", ""),
                        Function(sprt.save_recolor_info, picker),
                        Function(sprt.save_xyinitial)]
            textbutton "Save":
                tooltip "|Save this tag to the Tag dropdown to select later."
                sensitive (persistent.sprt_who
                    and persistent.sprt_who not in persistent.sprt_saved_recolor_tags)
                action [AddToSet(persistent.sprt_saved_recolor_tags, persistent.sprt_who),
                    Function(sprt.save_xyinitial),
                    Function(sprt.save_recolor_info, picker),
                    Notify("Saved!")]

    if GetFocusRect("tag_drop"):
        use sprt_dropdown("tag_drop"):
            style_prefix 'sprt_drop'
            for tg in sorted(persistent.sprt_saved_recolor_tags):
                hbox:
                    textbutton tg:
                        yalign 0.5 text_yalign 0.5
                        action [SetField(sprt, "what", ""),
                            Function(sprt.save_xyinitial),
                            Function(sprt.retrieve_xyinitial, tg),
                            SetScreenVariable('current_color', 0),
                            Function(sprt.fetch_recolor_info, tg, picker, mb),
                            SetField(persistent, "sprt_who", tg),
                            SetScreenVariable("recolored_img",
                                DynamicDisplayable(sprt.pick_multi_color,
                                    img=sprt.get_image(tg),
                                    picker=picker)),
                            Function(sprt.set_up_initial_state, picker),
                            ClearFocus("tag_drop")]
                    textbutton "(Remove)" size_group None:
                        background sprt.construct_frame(sprt.RED, sprt.MAROON, sprt.PADDING)
                        hover_background sprt.construct_frame(sprt.MAROON, sprt.RED, sprt.PADDING)
                        action [RemoveFromSet(persistent.sprt_saved_recolor_tags, tg)]
    elif GetFocusRect("other_drop"):
        use sprt_dropdown("other_drop"):
            style_prefix 'sprt_drop'
            for tg in sorted(persistent.sprt_saved_other_tags):
                hbox:
                    textbutton tg:
                        yalign 0.5 text_yalign 0.5
                        action [SetField(persistent, "sprt_extra", tg),
                            ClearFocus("other_drop")]
                    textbutton "(Remove)" size_group None:
                        background sprt.construct_frame(sprt.RED, sprt.MAROON, sprt.PADDING)
                        hover_background sprt.construct_frame(sprt.MAROON, sprt.RED, sprt.PADDING)
                        action [RemoveFromSet(persistent.sprt_saved_other_tags, tg)]
    elif GetFocusRect("rgb_drop"):
        add sprt.GRAY alpha 0.7
        dismiss action ClearFocus("rgb_drop")
        nearrect:
            focus "rgb_drop"
            frame:
                modal True style_prefix 'sprt_drop' xalign 0.5
                has vbox
                for chan in ("Gray", "Red", "Green", "Blue"):
                    textbutton chan:
                        yalign 0.5 text_yalign 0.5
                        sensitive persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False)
                        action [Function(sprt.switch_rgb_channels, picker, chan, mb),
                            SetScreenVariable('current_color', 0),
                            ClearFocus("rgb_drop")]
    elif GetFocusRect("threshold_drop") and sprt.check_input():
        nearrect:
            focus "threshold_drop" prefer_top True yalign 1.0 yoffset -sprt.YSPACER
            frame:
                modal True style_prefix 'sprt_drop' xalign 0.5
                xmaximum sprt.PICKER_SIZE
                has vbox
                text "Type or paste in a list of thresholds, separated by commas.":
                    style 'sprt_text' xalign 0.5 text_align 0.5
                add sprt.ORANGE ysize int(sprt.PADDING*0.5)
                text "Result:" style 'sprt_text'
                hbox:
                    text ', '.join([str(x) for x in sprt.thresholds[:sprt.num_shades]]):
                        style 'sprt_text' yalign 0.5
                    textbutton "Clear" action SetField(sprt, 'threshold_input', "")


    if enter_rgb_colorize:
        add sprt.GRAY alpha 0.8
        dismiss action [rgbc_input.Disable(),
            SetScreenVariable('enter_rgb_colorize', False)]
        frame:
            style_prefix 'sprt_save_swatch'
            xmaximum int(config.screen_width*0.7) + sprt.PADDING*4
            has vbox
            order_reverse True
            label "Copy-paste an RGBColorize object into the box":
                text_color sprt.ORANGE text_outlines [(1, "#000")]
            text "(Click anywhere outside the box to dismiss)" size sprt.SMALL_TEXT
            hbox:
                spacing sprt.PADDING*2 box_wrap False
                button:
                    style_prefix 'sprt_input'
                    key_events True
                    action rgbc_input.Toggle()
                    xmaximum int(config.screen_width*0.5)
                    input value rgbc_input allow sprt.INPUT_ALLOW+"()#[]\"',=":
                        copypaste True
                textbutton "Clear" style_prefix 'sprt_small':
                    action SetField(sprt, "rgbc_input", "")
            if sprt.rgbc_obj:
                vbox:
                    style_prefix 'rgbc_preview'
                    hbox:
                        label "Gray"
                        for i, col in enumerate(sprt.rgbc_obj.gray[:sprt.rgbc_obj.num_shades]):
                            imagebutton:
                                idle sprt.construct_frame(sprt.WHITE, col, sprt.PADDING)
                                xysize (sprt.XSPACER*2, sprt.XSPACER*2)
                                tooltip "{}: threshold = {}".format(col.hexcode, round(sprt.rgbc_obj.gray_thresh[i]*255))
                                action NullAction()
                    if sprt.rgbc_obj.gray != sprt.rgbc_obj.red:
                        hbox:
                            label "Red"
                            for i, col in enumerate(sprt.rgbc_obj.red[:sprt.rgbc_obj.red_num]):
                                imagebutton:
                                    idle sprt.construct_frame(sprt.WHITE, col, sprt.PADDING)
                                    xysize (sprt.XSPACER*2, sprt.XSPACER*2)
                                    tooltip "{}: threshold = {}".format(col.hexcode, round(sprt.rgbc_obj.red_thresh[i]*255))
                                    action NullAction()
                    if sprt.rgbc_obj.gray != sprt.rgbc_obj.green:
                        hbox:
                            label "Green"
                            for i, col in enumerate(sprt.rgbc_obj.green[:sprt.rgbc_obj.green_num]):
                                imagebutton:
                                    idle sprt.construct_frame(sprt.WHITE, col, sprt.PADDING)
                                    xysize (sprt.XSPACER*2, sprt.XSPACER*2)
                                    tooltip "{}: threshold = {}".format(col.hexcode, round(sprt.rgbc_obj.green_thresh[i]*255))
                                    action NullAction()
                    if sprt.rgbc_obj.gray != sprt.rgbc_obj.blue:
                        hbox:
                            label "Blue"
                            for i, col in enumerate(sprt.rgbc_obj.blue[:sprt.rgbc_obj.blue_num]):
                                imagebutton:
                                    idle sprt.construct_frame(sprt.WHITE, col, sprt.PADDING)
                                    xysize (sprt.XSPACER*2, sprt.XSPACER*2)
                                    tooltip "{}: threshold = {}".format(col.hexcode, round(sprt.rgbc_obj.blue_thresh[i]*255))
                                    action NullAction()
                    null height sprt.YSPACER
                    hbox:
                        spacing sprt.XSPACER
                        textbutton "Apply":
                            style_prefix 'sprt_small' xalign 0.5
                            action [Function(sprt.apply_rgbc, sprt.rgbc_obj,
                                    picker, mb),
                                rgbc_input.Disable(),
                                SetScreenVariable('enter_rgb_colorize', False)]
                        textbutton "Cancel":
                            style_prefix 'sprt_small' xalign 0.5
                            action [rgbc_input.Disable(),
                                SetScreenVariable('enter_rgb_colorize', False)]

    key 'K_ESCAPE' action [DisableAllInputValues(), ClearFocus('threshold_drop')]

    on 'hide' action [Function(sprt.save_recolor_info, picker),
        Function(sprt.save_xyinitial)]
    on 'replaced' action [Function(sprt.save_recolor_info, picker),
        Function(sprt.save_xyinitial)]

    if not renpy.get_screen("sprt_colorize_tutorial"):
        use hamburger_menu():
            style_prefix 'hamburger'
            use sprt_recolorize_save_load()
            textbutton _("Return") action Return()
            textbutton "How to Use" action Show("sprt_colorize_tutorial")

    $ tooltip = GetTooltip()
    if isinstance(tooltip, basestring) and tooltip:
        nearrect:
            focus "tooltip"
            frame:
                ## Delay the appearance of informational tooltips so they don't
                ## interrupt the user's flow.
                if tooltip.startswith("|"):
                    at transform:
                        alpha 0.0
                        1.8
                        alpha 1.0
                style_prefix 'sprt_drop' xalign 0.5
                text "{}".format(tooltip if not tooltip.startswith("|") else tooltip[1:]):
                    style 'sprt_text' xmaximum sprt.PICKER_SIZE layout "subtitle"

## EXTRAS SCREENS ##############################################################
## These screens will be overwritten by the extra QoL file, if included.
init -999:
    screen sprt_add_colorize_comparison():
        pass
    screen sprt_viewport_extras(recolored_img):
        add recolored_img:
            align (0.5, 0.5)
            if sprt.within_range(persistent.sprt_zoom_dict.setdefault(
                    persistent.sprt_who, 1.0), 1.0):
                ## Bizarre workaround for strange stretching on zoom 1.0
                zoom 1.0000000001
            else:
                zoom persistent.sprt_zoom_dict.get(persistent.sprt_who,
                    1.00000000001)
    screen sprt_recolor_tab2(*args, **kwargs):
        pass
    screen sprt_recolor_tab3(*args, **kwargs):
        pass
    screen sprt_saving_swatches_screen(*args, **kwargs):
        pass
    screen sprt_recolorize_save_load():
        pass

## TAB 1: ######################################################################
## Contains the picker and threshold sliders.
screen sprt_recolor_tab1(picker, mb, current_color, enter_rgb_colorize, rgbc_input):
    ## The current swatch, tracking the picker colour
    default picker_swatch = DynamicDisplayable(sprt.current_picker_color,
        picker=picker, xsize=sprt.SWATCH_SQUARE_SIZE,
        ysize=sprt.SWATCH_SQUARE_SIZE)
    ## The current hexcode, tracking the picker colour
    default picker_hex = DynamicDisplayable(sprt.display_hexcode, picker=picker)
    ## An input value for inputting a new hexcode
    default hex_input = SpecialInputValue(sprt, 'hexcode',
        set_callback=sprt.check_hex(picker=picker),
        enter_callback=Function(sprt.update_hex, picker=picker))
    ## The threshold bars, for the non-multibar approach
    default threshold_bar = DynamicDisplayable(sprt.static_gradient_bar,
        picker=picker)
    default threshold_input = SpecialInputValue(sprt, 'threshold_input',
        set_callback=sprt.check_threshold_input(mb=mb),
        enter_callback=Function(renpy.run,
            [SetField(sprt, 'threshold_input', ""),
            sprt.record_threshold_state,
            ClearFocus('threshold_drop')]))

    frame:
        background None padding (0, 0) style 'empty'
        modal True align (0.5, 0.5)
        has hbox
        style_prefix 'sprt_color'
        frame:
            if sprt.check_input():
                foreground Transform(sprt.GRAY, alpha=0.7)
            has fixed
            ## A vertical bar which lets you change the hue of the picker.
            vbar:
                if not sprt.check_input(hex_input):
                    value FieldValue(picker, "hue_rotation", 1.0)
                    released Function(sprt.record_swatch_state, picker)
                else:
                    value 1 range 2 style 'sprt_color_vbar'

        ## The picker itself
        vbox:
            spacing sprt.PADDING*3
            frame:
                if sprt.check_input():
                    foreground Transform(sprt.GRAY, alpha=0.7)
                has fixed
                if sprt.check_input():
                    add "#888" xysize (sprt.PICKER_SIZE, sprt.PICKER_SIZE)
                else:
                    add picker

            if sprt.num_shades > 1:
                ############################################################
                ## If you have the Multi-Thumb Bar code from my itch.io
                ## (https://feniksdev.itch.io/multi-thumb-bar-for-renpy)
                ## then it will be used here:
                ############################################################
                if not isinstance(mb, Text):
                    frame:
                        if sprt.check_input():
                            foreground Transform(sprt.GRAY, alpha=0.7)
                        has fixed
                        if sprt.check_input():
                            add "#888" xysize (sprt.PICKER_SIZE, sprt.PICKER_BAR_WIDTH)
                        else:
                            add mb
                ############################################################
                ## Otherwise, these bars allow you to adjust the same
                ## values. If you have the Multi-Thumb Bar code from my
                ## itch.io, you can remove this part in favour of the
                ## earlier code:
                ############################################################
                else:
                    frame:
                        if sprt.check_input():
                            foreground Transform(sprt.GRAY, alpha=0.7)
                        has fixed
                        bar style 'sprt_shade_bar_bar':
                            if sprt.check_input():
                                value 1 range 2
                            else:
                                value sprt.ThresholdValue(sprt.thresholds,
                                    current_color, 255)
                            bar_invert True base_bar threshold_bar
                            released sprt.record_threshold_state
                        ## "Phantom" bars with the values of the other
                        ## thresholds.
                        for i in range(sprt.num_shades):
                            if i != current_color:
                                bar:
                                    value sprt.thresholds[i] range 255
                                    bar_invert True base_bar Null()
                                    thumb_offset int(sprt.PADDING*1.5)
                                    thumb Transform("selector_bg",
                                        xysize=(sprt.PADDING*3, sprt.PICKER_BAR_WIDTH),
                                        alpha=0.35)
                                    style 'sprt_shade_bar_bar'
                ############################################################
                null height 0
            if sprt.num_shades > 1:
                button:
                    style_prefix 'sprt_input'
                    if not sprt.check_input(threshold_input) and sprt.check_input():
                        foreground Transform(sprt.GRAY, alpha=0.7)
                        sensitive False
                    else:
                        foreground Text("Thresholds: {}".format(', '.join(
                            [str(x) for x in sprt.thresholds[:sprt.num_shades]])),
                            style='sprt_threshold_input_text')
                        selected_foreground None
                        idle_child Text("", style='sprt_threshold_input_text')
                        hover_child Text("", style='sprt_threshold_input_text')
                        selected_child None
                        selected_hover_child None
                    key_events True xsize sprt.PICKER_SIZE
                    tooltip "|Enter a list of thresholds to apply to the image. Separate each threshold number with a comma and/or space. Thresholds can go from 0-255, and each threshold must be lower than or equal to the one before it."
                    selected sprt.check_input(threshold_input)
                    action [SetField(sprt, 'threshold_input', ", ".join(
                            [str(x) for x in sprt.thresholds[:sprt.num_shades]])),
                        If(sprt.check_input(threshold_input),
                            [threshold_input.Disable(),
                            ClearFocus('threshold_drop')],
                            [threshold_input.Enable(),
                            CaptureFocus("threshold_drop")])]
                    at transform:
                        crop (0.0, 0.0, 1.0, 1.0)
                    input value threshold_input text_align 1.0 copypaste True:
                        allow "0123456789, " xalign 1.0 layout 'nobreak'
                        color "#000" caret 'sprt_caret'
            hbox:
                textbutton "Reset":
                    if sprt.check_input():
                        foreground Transform(sprt.GRAY, alpha=0.7)
                        sensitive False
                    tooltip "|Reset the thresholds on the bar to their default values."
                    style_prefix 'sprt_small'
                    action Function(sprt.reset_thresholds, mb)
                textbutton "Copy":
                    if sprt.check_input():
                        foreground Transform(sprt.GRAY, alpha=0.7)
                        sensitive False
                    tooltip "|Copy the threshold numbers to the clipboard."
                    style_prefix 'sprt_small'
                    action Function(sprt.copy_thresholds)
            textbutton "RGBColorize Input":
                if sprt.check_input():
                    foreground Transform(sprt.GRAY, alpha=0.7)
                    sensitive False
                tooltip "|Input an RGBColorize object to recolour the image with."
                style_prefix 'sprt_small' xalign 0.5
                action [SetField(sprt, 'rgbc_input', ""),
                    SetField(sprt, 'rgbc_obj', None),
                    SetScreenVariable('enter_rgb_colorize', True),
                    rgbc_input.Enable()]

        vbox:
            style_prefix 'sprt_swatch'
            xsize sprt.SWATCH_WIDTH spacing 0
            button:
                style 'empty' padding (0, 0)
                if sprt.check_input():
                    foreground Transform(sprt.GRAY, alpha=0.7)
                    action NullAction()
                has hbox
                style_prefix 'sprt_rgb_switch'
                textbutton "{}".format(
                        "✗" if not persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who) else "✔"):
                    if sprt.check_input():
                        sensitive False
                    tooltip "|Toggle RGB editing mode on and off (currently {})".format(
                        "off" if not persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who) else "on")
                    selected persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False)
                    action [Function(sprt.toggle_rgb_recolorize, picker, mb),
                        SetScreenVariable('current_color', 0)]
                textbutton "{}▼".format(
                        persistent.sprt_rgb_channel if persistent.sprt_rgb_recolorize_on.get(
                            persistent.sprt_who, False) else "Gray"):
                    style_prefix 'sprt_rgb_dropdown'
                    if sprt.check_input():
                        sensitive False
                    else:
                        sensitive persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False)
                    tooltip "|In RGB editing mode, you can choose which colour channel to change the colours for. Gray is for the base gray colours, from black to white."
                    action CaptureFocus("rgb_drop")
                textbutton "⟳" selected True:
                    if sprt.check_input():
                        sensitive False
                    else:
                        sensitive (persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False)
                            and persistent.sprt_rgb_channel != "Gray")
                    tooltip "|Reset this channel's swatches to match the default swatches."
                    action [Function(sprt.reset_rgb_channel, picker,
                            persistent.sprt_rgb_channel, mb),
                        SetScreenVariable('current_color', 0)]
            null height sprt.PADDING
            button:
                style_prefix 'sprt_hex_input'
                key_events True
                sensitive not sprt.check_input() or sprt.check_input(hex_input)
                insensitive_foreground "#888"
                ## The DynamicDisplayable with the hexcode
                idle_child picker_hex hover_child picker_hex
                selected sprt.check_input(hex_input)
                selected_idle_child None selected_hover_child None
                action [SetField(sprt, 'hexcode', ""), hex_input.Toggle()]
                input value hex_input:
                    prefix "#" allow "0123456789abcdefABCDEF"
                    length 8 copypaste True caret 'sprt_caret'
            null height sprt.PADDING*2
            ## The swatches
            for i in range(MAX_COLORIZE_COLORS):
                use sprt_swatch(picker, current_color, picker_swatch, hex_input, i, mb)
                if i < MAX_COLORIZE_COLORS-1:
                    ## A button to switch adjacent colours
                    textbutton "⇅":
                        tooltip "|Swap this swatch with the one below it."
                        if sprt.check_input():
                            foreground Transform(sprt.GRAY, alpha=0.7)
                            sensitive False
                        else:
                            sensitive sprt.num_shades-1 > i
                        style_prefix 'sprt_swap'
                        action [Function(sprt.swap_swatch, picker, i, mb),
                            SetScreenVariable('current_color', 0)]

## CURRENT SWATCH SCREEN: ######################################################
screen sprt_swatch(picker, current_color, picker_swatch, hex_input, num, mb):
    if sprt.num_shades > num:
        hbox:
            spacing sprt.PADDING*3
            if current_color == num:
                frame:
                    ## Shows the currently selected colour.
                    if sprt.check_input():
                        foreground Transform(sprt.GRAY, alpha=0.7)
                    add picker_swatch
                    if not sprt.check_input():
                        key 'K_DELETE':
                            action Function(sprt.remove_swatch, picker, num, mb)
            else:
                button:
                    if sprt.check_input():
                        foreground Transform(sprt.GRAY, alpha=0.7)
                        sensitive False
                    style 'sprt_swatch_image_button'
                    add picker.get_color(num)
                    ## Switch the picker to track this colour.
                    action [Function(picker.save_color, current_color),
                        hex_input.Disable(),
                        SetScreenVariable("current_color", num),
                        Function(picker.swap_to_saved_color, num)]
                    if not sprt.check_input():
                        key 'K_DELETE':
                            action Function(sprt.remove_swatch, picker, num, mb)
            button:
                ## A button to copy the colour code to the clipboard.
                style_prefix 'sprt_small'
                tooltip "|Copy this swatch's colour code to the clipboard."
                action Function(sprt.copy_color, picker, num)
                if sprt.check_input():
                    foreground Transform(sprt.GRAY, alpha=0.7)
                    sensitive False
                add Fixed(
                    Text("□", style="sprt_small_button_text"),
                    Text("■", style="sprt_small_button_text",
                        offset=(int(sprt.PADDING*1.5), int(sprt.PADDING*1.5))),
                    fit_first=True
                ) align (0.5, 0.5) offset (-int(sprt.PADDING*0.75), -sprt.PADDING)
            if sprt.num_shades > 1:
                ## Remove this swatch
                textbutton "✗":
                    if sprt.check_input():
                        foreground Transform(sprt.GRAY, alpha=0.7)
                        sensitive False
                    style_prefix 'sprt_small'
                    tooltip "|Remove this swatch from the recolouring process."
                    action Function(sprt.remove_swatch, picker, num, mb)
    else:
        imagebutton:
            idle "#888"
            if sprt.check_input():
                foreground Transform(sprt.GRAY, alpha=0.7)
                sensitive False
            foreground Text("+", style='sprt_text', color="#fff",
                outlines=[(4, "#000")], size=sprt.BIG_TEXT,
                align=(0.5, 0.5))
            hover_foreground Text("+", style='sprt_text', color="#000",
                outlines=[(4, "#fff")], size=sprt.BIG_TEXT,
                align=(0.5, 0.5))
            tooltip "|Add a new swatch to the recolouring process."
            action [SetScreenVariable('current_color', sprt.num_shades),
                Function(sprt.add_swatch, picker, mb)]

################################################################################
## STYLES
################################################################################

style sprt_load_json_frame:
    is empty
    background None padding (0, 0)
    modal True align (0.5, 0.5)
style sprt_load_json_hbox:
    is empty
    align (0.5, 0.5)
    spacing sprt.XSPACER
style sprt_load_json_vbox:
    is empty
    align (0.5, 0.5)
    spacing sprt.YSPACER*2
style sprt_load_json_label:
    is empty
    align (0.5, 0.5)
style sprt_load_json_label_text:
    is sprt_text
    size sprt.BIG_TEXT
    align (0.5, 0.5)
    color sprt.ORANGE
    text_align 0.5
style sprt_load_json_text:
    is sprt_text
    align (0.5, 0.5) text_align 0.5
style sprt_load_json_button:
    is empty
    align (0.5, 0.5)
    background sprt.construct_frame(sprt.RED, "#0000", sprt.PADDING)
    hover_background sprt.construct_frame(sprt.RED, sprt.MAROON, sprt.PADDING)
    padding (sprt.PADDING*3, sprt.PADDING*3)
style sprt_load_json_button_text:
    is sprt_text

style sprt_rgb_switch_hbox:
    spacing sprt.PADDING*3
    xalign 0.5 yalign 0.5
style sprt_rgb_switch_text:
    is sprt_text
    yalign 0.5
    size sprt.SMALL_TEXT
    text_align 0.5 xalign 0.5
    min_width int(sprt.SWATCH_WIDTH*0.7)
style sprt_rgb_switch_button:
    is sprt_small_button
    selected_background sprt.construct_frame(sprt.YELLOW, sprt.BLUE, sprt.PADDING)
    selected_hover_background sprt.construct_frame(sprt.DARK_ORANGE, sprt.BLUE, sprt.PADDING)
    background sprt.construct_frame("#888", "#0000", sprt.PADDING)
    insensitive_background sprt.construct_frame("#888", "#0000", sprt.PADDING)
    selected_insensitive_background sprt.construct_frame("#888", "#0000", sprt.PADDING)
    hover_background sprt.construct_frame(sprt.YELLOW, "#0000", sprt.PADDING)
    ypadding int(sprt.PADDING*0.7)
style sprt_rgb_switch_button_text:
    is sprt_small_button_text
    size sprt.SMALL_TEXT
    insensitive_color "#888"
    insensitive_outlines []
style sprt_rgb_dropdown_button:
    padding (0, 0)
style sprt_rgb_dropdown_button_text:
    is sprt_rgb_switch_text
    hover_color sprt.YELLOW
    hover_underline True
style sprt_blend_button:
    background sprt.construct_checkbox(sprt.RED, inside="#000d",
        width=sprt.PADDING, box_size=(sprt.SPACER, sprt.SPACER), checked=False)
    selected_background sprt.construct_checkbox(sprt.RED, inside="#000d",
        width=sprt.PADDING, box_size=(sprt.SPACER, sprt.SPACER), checked=True)
    left_padding sprt.SPACER+sprt.PADDING*2
    align (0.5, 0.5)
style sprt_blend_button_text:
    is sprt_text
    align (0.5, 0.5)

style sprt_colorize_vp_viewport:
    xsize int(sprt.PICKER_SIZE*0.8) xfill False
    yfill True
style sprt_colorize_vp_hbox:
    spacing sprt.PADDING*2 xalign 0.5
    xmaximum int(sprt.PICKER_SIZE*0.75) box_wrap True
    box_wrap_spacing sprt.PADDING
style sprt_colorize_vp_vbox:
    spacing sprt.PADDING*2
    xsize int(sprt.PICKER_SIZE*0.75)
style sprt_colorize_vp_button:
    xalign 0.5
    background sprt.construct_frame(sprt.ORANGE, "#0000", sprt.PADDING)
    hover_background sprt.construct_frame(sprt.YELLOW, sprt.YELLOW, sprt.PADDING)
    hover_foreground Text("SWAP", color=sprt.GRAY, bold=True, align=(0.5, 0.5),
        font="DejaVuSans.ttf", size=sprt.SMALL_TEXT, text_align=0.5)
    insensitive_background sprt.construct_frame("#fff5", "#0000", sprt.PADDING)
    padding (sprt.PADDING*2, sprt.PADDING*2)
style sprt_colorize_vp_button_text:
    is sprt_text
    hover_color sprt.YELLOW
    insensitive_color "#fff5"
style sprt_colorize_vp_vscrollbar:
    base_bar sprt.MAROON
    thumb sprt.RED xsize sprt.PADDING*3
    unscrollable "hide"

style sprt_shade_bar_vbox:
    spacing sprt.PADDING
style sprt_shade_bar_bar:
    left_bar "#888" right_bar "#888"
    xsize sprt.PICKER_SIZE
    ysize sprt.PICKER_BAR_WIDTH
    thumb Transform("selector_bg", xysize=(sprt.PADDING*4, sprt.PICKER_BAR_WIDTH))
    thumb_offset sprt.PADDING*2

style sprt_color_frame:
    is empty
    background sprt.construct_frame("#fff", "#0000")
    padding (sprt.PADDING, sprt.PADDING)
style sprt_color_hbox:
    spacing sprt.PADDING*3 xalign 0.5 yalign 0.5
style sprt_color_fixed:
    fit_first True
style sprt_color_vbar:
    xysize (sprt.PICKER_BAR_WIDTH, sprt.PICKER_SIZE)
    base_bar At(Transform("#000",
            xysize=(sprt.PICKER_BAR_WIDTH, sprt.PICKER_SIZE)),
        spectrum(horizontal=False))
    thumb Transform("selector_bg", xysize=(sprt.PICKER_BAR_WIDTH, sprt.PADDING*4))
    thumb_offset sprt.PADDING*2

style sprt_threshold_input_text:
    is sprt_text
    adjust_spacing False yalign 0.5
    color "#000" xalign 0.5 size sprt.SMALL_TEXT

style sprt_color_bar:
    xysize (sprt.PICKER_SIZE, sprt.PICKER_BAR_WIDTH)
    base_bar At(Transform("#000",
            xysize=(sprt.PICKER_SIZE, sprt.PICKER_BAR_WIDTH)),
        color_picker("#f00", "#f00", "#888", "#888"))
    thumb Transform("selector_bg", xysize=(sprt.PADDING*4, sprt.PICKER_BAR_WIDTH))
    thumb_offset sprt.PADDING*2

style sprt_save_swatch_frame:
    is empty
    padding (sprt.PADDING*2, sprt.PADDING*2)
    background sprt.construct_frame(sprt.RED, sprt.GRAY, sprt.PADDING)
    align (0.5, 0.5)
    xmaximum sprt.PICKER_FRAME_SIZE
style sprt_save_swatch_vbox:
    is empty
    spacing sprt.PADDING*2
style sprt_save_swatch_label:
    align (0.5, 0.5)
style sprt_save_swatch_text:
    is sprt_text
    layout 'subtitle' align (0.5, 0.5)
    text_align 0.5
style sprt_save_swatch_label_text:
    is sprt_text
    xalign 0.5
    text_align 0.5
    color sprt.WHITE
    layout 'subtitle'
    size sprt.BIG_TEXT
style sprt_save_swatch_hbox:
    is empty
    spacing sprt.PADDING
    align (0.5, 0.5)
    box_wrap True
    box_wrap_spacing sprt.PADDING*2
    xmaximum sprt.PICKER_FRAME_SIZE - sprt.PADDING*3
style sprt_save_swatch_button:
    is empty
    background "#fff3"
    selected_background sprt.DARK_ORANGE
    hover_background sprt.ORANGE
    padding (sprt.PADDING, sprt.PADDING)

style sprt_swap_button:
    is empty
    xsize sprt.SWATCH_SQUARE_SIZE+sprt.PADDING*2
style sprt_swap_button_text:
    is sprt_small_button_text
    hover_color sprt.ORANGE
    insensitive_color "#888"
    insensitive_outlines []
    text_align 0.5 xalign 0.5 yalign 0.5
    size int(sprt.MED_TEXT*0.9)

style sprt_hex_input_button:
    is sprt_input_button
    xalign 0.0
    hover_foreground "#fff2"
    xsize int(sprt.SWATCH_WIDTH*1.6)
style sprt_hex_input_button_text:
    is sprt_input_button_text
style sprt_hex_input_input:
    is sprt_input_input

style sprt_swatch_button:
    is empty
    padding (sprt.PADDING, sprt.PADDING)
    insensitive_background sprt.RED
    background sprt.RED
style sprt_swatch_button_text:
    is sprt_text
    color "#aaa"
    hover_color "#fff"
    xysize (sprt.SWATCH_SQUARE_SIZE+sprt.PADDING*2, sprt.SWATCH_SQUARE_SIZE+sprt.PADDING*2)
style sprt_swatch_image_button:
    xysize (sprt.SWATCH_SQUARE_SIZE+sprt.PADDING*2, sprt.SWATCH_SQUARE_SIZE+sprt.PADDING*2)
    padding (sprt.PADDING, sprt.PADDING)
    background sprt.construct_frame(sprt.WHITE, "#0000", sprt.PADDING)
    hover_foreground sprt.construct_frame(sprt.RED, "#0000", sprt.PADDING)
style sprt_swatch_frame:
    xysize (sprt.SWATCH_SQUARE_SIZE+sprt.PADDING*2, sprt.SWATCH_SQUARE_SIZE+sprt.PADDING*2)
    padding (sprt.PADDING, sprt.PADDING)
    background sprt.construct_frame(sprt.RED, "#0000", sprt.PADDING)

style sprt_preview_vbox:
    spacing sprt.PADDING*3
    xalign 0.5
style sprt_preview_frame:
    is sprt_color_frame
style sprt_preview_fixed:
    is sprt_color_fixed
style sprt_preview_bar:
    is sprt_zoom_bar
    ysize sprt.YSPACER*2+sprt.PADDING*2
    xalign 0.5
style sprt_preview_text:
    is sprt_zoom_text
style sprt_preview_button:
    is sprt_colorize_vp_button
    hover_foreground Text("X", color=sprt.RED, bold=True, align=(0.5, 0.5),
        font="DejaVuSans.ttf", size=sprt.MED_TEXT)
    hover_background sprt.construct_frame(sprt.RED, sprt.MAROON, sprt.PADDING)
style sprt_preview_button_text:
    is sprt_colorize_vp_button_text
    hover_color sprt.RED

style rgbc_preview_vbox:
    spacing sprt.YSPACER
    xalign 0.5
style rgbc_preview_label:
    align (0.5, 0.5)
    size_group "rgbc_preview"
style rgbc_preview_label_text:
    is sprt_text
    color sprt.ORANGE xalign 1.0 text_align 1.0
    outlines [(2, "#000")]
style rgbc_preview_hbox:
    spacing sprt.YSPACER
    align (0.0, 0.5)

################################################################################
## TUTORIAL
################################################################################
## Note that this is coded in a pretty specific way due to the flexibility
## of the tool. It's not meant to be a good example of how to code a screen,
## in particular due to the repeated code. Normally it would be easier to
## have images showing highlighted areas of the screen, which isn't possible
## here due to how the tool adapts to different projects + I didn't want to
## include unnecessary images in the tool.
################################################################################
init 40 python in sprt:
    ## A special way of declaring the tutorial text in order to make it easy
    ## to add or remove text without having to change the code.
    tut5 = Tutorial(
        TutorialText("intro", "Welcome to the tutorial for the Colorize tool!",
        "This tutorial will show you how to use the tool to recolour images. Unlike other tutorials for image tools, you will be able to use the buttons in the colorize tool during this tutorial to follow along.",
        "Make sure you have the image \"hand_rgb.png\" in your image folder before proceeding. You can press ESCAPE at any time to close the tutorial.",
        xalign=0.5, final_txt=None),
        TutorialText("tag1", "Bringing up the image",
        "First, you need to type in the image to view it. Type \"hand_rgb\" into the input box beside the \"Tag\" button in the top left.",
        "You can press \"Continue\" once you have completed this.",
        xalign=1.0, final_txt=None),
        TutorialText("image_basics", "Image Basics",
        "Now that you've typed in the image, it should appear in the center of the screen. You can click and drag with your mouse to move it around so you can see it better.",
        "You can also use the \"Re-center\" button to center the image if you lose it, and use the mousewheel or the zoom bar at the bottom to make it smaller or larger.",
        "Make sure the image is visible to the left and press \"Continue\".",
        xalign=1.0, final_txt=None),
        TutorialText("picker1", "Using the Colour Picker",
        "To the right of the screen is a colour picker. You can select a swatch from the right, and then click and drag around the central square to pick a colour and see it applied when recolouring your image.",
        "Try selecting the top colour, and then dragging your mouse around the colour picker square. You should see the image change colour as you do so.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("thresh1", "Colour Thresholds",
        "You might notice only some parts of the image are changing colour. That's because each colour has a threshold, which determines which shades of gray it applies to.",
        "By default, the top swatch corresponds to the lightest shades of gray (including white), and the bottom swatch corresponds to the darkest shades of gray (including black).",
        "Anything above a colour's threshold gets mixed with the colour above it, and anything below a colour's threshold gets mixed with the colour below it.",
        "These thresholds can be adjusted with the bar below the colour picker. You can also use the \"Reset\" button to reset them to their default values.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("thresh2", "Colour Thresholds 2",
        "To help you understand what's happening, add or remove swatches (you can add new swatches by clicking a swatch with {b}+{/b} and remove them with the \"✗\" next to the swatch) until you have three swatches. Make the top colour a {color=#f00}vivid red{/color}, the middle colour a {color=#0f0}vivid green{/color}, and the bottom colour a {color=#00f}vivid blue{/color} (if you want colour codes, that's #F00, #0F0, and #00F).",
        "Reset the thresholds to their defaults with the \"Reset\" button. If you have the Multi-Thumb Bar code, all three bar thumbs will be adjustable - you want to move the middle thumb. If you do not have the multi-thumb bar code, click on the green swatch to highlight the middle thumb on the bar. Move the thumb to the right until it's nearly 0.",
        "You'll notice that this makes the image mostly red, with the green showing mostly around the outlines of the hand.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("thresh3", "Colour Thresholds 3",
        "The reason the green shows up best around the outlines is because the green threshold is now very low, near the darkest shades of gray (aka the black line art). Anything lighter than the threshold gets mixed with the next colour (red), so most colours are a mix between red and green. The base grayscale image has a lot of light shades of gray, so the final image mixes more red than green in most areas.",
        "Now try dragging the green (middle) threshold to the left until it's nearly 255. You'll notice that the image becomes mostly green, and the blue is used for those outlines instead. The red shows up only for a little bit of the highlight on the nails.",
        "This is because now most colours are under the green threshold, so the green gets mixed in with the blue.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("thresh4", "Colour Thresholds 4",
        "Many images do not have the full range of colours from pure white to pure black, so you will need to adjust the thresholds to match the shades your image actually uses. If you don't see one of your colours appearing on your image, usually that indicates your threshold is too high or too low.",
        "The threshold numbers go from 0 to 255 and correspond to the highest red/green/blue (RGB) value of the image. Most colour eyedropper tools will tell you the RGB value of a colour code - you can use that to know where to put the threshold.",
        "For example, if the lightest colour in your base grayscale image has an RGB of (240, 240, 240), then you would set the top/lightest threshold to 240. If the darkest colour in your image has an RGB of (20, 20, 20), then you would set the bottom/darkest threshold to 20.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("rgb1", "RGB Editing Mode",
        "This tool can also tell apart red, green, and blue in a grayscale image. How to set up an image for RGB recolorizing is its own tutorial topic, but luckily the hand_rgb image is already set up with it. Toggle on RGB mode by clicking the \"✗\" button above the hexcode input box.",
        "You can click Continue after you've toggled RGB editing mode on.",
        xalign=0.0, xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("rgb2", "RGB Editing Mode 2",
        "By default, you might not see any changes when turning RGB editing mode on. That's because the tool will start off all the channels with the same set of colours you were using for the gray channel.",
        "However, you will start to see a difference when changing the colours now. Pick a swatch and play around with the colours.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("rgb3", "RGB Editing Mode 3",
        "You may notice that parts of the inside of the palm and index finger are not changing colour, nor are the fingernails.",
        "This is because the fingernails are using the green channel, and the palm is using the red channel. So, the reddest and greenest parts don't get recoloured by changing the colours in the gray channel.",
        "Specifically, the base image looks like the image on the right.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("rgb4", "RGB Editing Mode 4",
        "To adjust these colours, you will need to switch to the red and green channels. You can do so by hitting the dropdown next to the button where you turned on RGB editing. It should say \"Gray\" by default.",
        "Switch over to the green channel now to edit the fingernail colour. You can click Continue once you've done so.",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("rgb5", "RGB Editing Mode 5",
        "As with editing the gray channel colours, you can edit the red, green, and blue channels the same way by picking a swatch and using the colour picker to adjust it. You can even adjust the thresholds and number of colours separately from the other channels.",
        "Try adjusting the green channel colours now. You should see the fingernails change colour as you do so, but not the rest of the image.",
        "Note also that even though the fingernails are green in the base image, and we're using the green channel to recolour them, you're not limited to greens when recolouring it. You can use whichever colours you want. That's because the green in the image is only used to tell it apart from equivalent shades of gray. It doesn't actually have to be green in the final recolour.",
        "You can also reset the red, green, and blue channels to be equal to the gray channel again by hitting the ⟳ button next to the channel name (the one inside the box under the \"(Drag to move)\" text, not the one at the top of the screen - that ⟳ is the redo button).",
        xalign=0.0, ymaximum=config.screen_height//3, yalign=1.0,
        xsize=config.screen_width-PICKER_FRAME_SIZE, final_txt=None),
        TutorialText("copy1", "Copying Colours",
        "Once you've landed on a colour combination you like, you can use the \"Copy Colors\" button in the top right corner to copy a special {b}RGBColorize{/b} object to the clipboard. This can be used as part of a list to smoothly interpolate between (example in {b}dynamic_colors.rpy{/b}), or you can add {b}.transform{/b} to the end of it to apply it to an image directly as a transform.",
        "This RGBColorize object can be copy-pasted into the input box that comes up when you hit the \"RGBColorize Input\" button under the thresholds, which will read the fields and set up the colours and thresholds to match it.",
        "You can also use the undo/redo buttons at the top of the screen do undo/redo a limited number of colour and threshold changes.",
        xalign=0.0, final_txt=None),
        TutorialText("extra1", "Conclusion",
        "And those are the main tools you'll need to start recolouring images! There are a great many features omitted from this tutorial for brevity, but you can keep an eye on {a=https://feniksdev.com/}feniksdev.com{/a} for more tutorials on the tool and how to set up your base images.",
        "Most buttons have a tooltip if you hover over it for a short while, which has extra information on what it does.",
        "There are many, many quality-of-life features included in the optional Colorize Tool Extras file, which you can find on my {a=https://feniksdev.itch.io/}itch.io{/a}, including saving swatches, image layers, preview/comparison images, saving colorize values to a file so you can safely delete persistent and load them again, and more.",
        "Thank you for trying out the tool! I hope you find it useful.",
        xalign=0.5, final_txt=None),
    )
screen sprt_colorize_tutorial():
    zorder 10

    on 'show' action SetField(persistent, 'sprt_tutorial5_shown', True)
    on 'replace' action SetField(persistent, 'sprt_tutorial5_shown', True)
    default step = 0
    default tut_adj = ui.adjustment()
    default tutorial = sprt.tut5

    key "K_ESCAPE" action Hide("sprt_colorize_tutorial")

    frame:
        style_prefix "sprt_tut"
        modal True background "#000d"
        properties tutorial.tut(step).properties
        viewport:
            mousewheel True scrollbars "vertical" yadjustment tut_adj
            fixed:
                if tutorial.tut(step).properties.get('xsize', None) is not None:
                    xsize tutorial.tut(step).properties['xsize']-sprt.PADDING*8
                if tutorial.tut(step).properties.get('ysize', None) is not None:
                    ysize tutorial.tut(step).properties['ysize']-sprt.PADDING*4
                else:
                    fit_first "height"
                hbox:
                    xalign 0.5 xmaximum tutorial.tut(step).properties.get('xsize', None)
                    vbox:
                        if tutorial.tut(step).id in ("thresh2", 'thresh3', 'rgb3'):
                            xsize 0.6
                        label tutorial.tut(step).title
                        for txt in tutorial.tut(step).text:
                            text txt
                        hbox:
                            xalign 0.5 spacing sprt.XSPACER
                            textbutton "Back":
                                style_prefix 'sprt_small'
                                sensitive (step > 0)
                                action SetScreenVariable('step', step-1)
                            textbutton "Continue":
                                style_prefix 'sprt_small'
                                if tutorial.tut(step).id == "tag1" and persistent.sprt_who != "hand_rgb":
                                    sensitive False
                                elif tutorial.tut(step).id == "rgb1" and not persistent.sprt_rgb_recolorize_on.get(persistent.sprt_who, False):
                                    sensitive False
                                elif tutorial.tut(step).id == "rgb4" and persistent.sprt_rgb_channel != "Green":
                                    sensitive False
                                action If(step < tutorial.length-1,
                                    [SetScreenVariable('step', step+1),
                                    tut_adj.change(0.0)],
                                    Hide("sprt_colorize_tutorial"))
                    if tutorial.tut(step).id == 'thresh2':
                        vbox:
                            add 'hand_rgb' at RGBColorize(
                                    ["#ff0000", "#00ff00", "#0000ff"],
                                    [255, 128, 0]).transform:
                                ysize config.screen_height//3 fit 'contain'
                            add 'hand_rgb' at RGBColorize(
                                    ["#ff0000", "#00ff00", "#0000ff"],
                                    [255, 0, 0]).transform:
                                ysize config.screen_height//3 fit 'contain'
                    elif tutorial.tut(step).id == 'thresh3':
                        vbox:
                            add 'hand_rgb' at RGBColorize(
                                    ["#ff0000", "#00ff00", "#0000ff"],
                                    [255, 0, 0]).transform:
                                ysize config.screen_height//3 fit 'contain'
                            add 'hand_rgb' at RGBColorize(
                                    ["#ff0000", "#00ff00", "#0000ff"],
                                    [255, 255, 0]).transform:
                                ysize config.screen_height//3 fit 'contain'
                    elif tutorial.tut(step).id == 'rgb3':
                        vbox:
                            add 'hand_rgb':
                                ysize config.screen_height//3 fit 'contain'


################################################################################
## Code to remove these files for a distributed game. Do not remove.
init python:
    build.classify("**colorize_tool.rpy", None)
    build.classify("**colorize_tool.rpyc", None)
################################################################################
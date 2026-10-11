// Shared constants for the certificate template editor. Keep in sync with
// lms/lms/certificate_renderer.py.

export const PAGE_SIZES = {
	A4: { width: 297, height: 210 },
	Letter: { width: 279.4, height: 215.9 },
}

export const getPageSize = (pageSize, orientation) => {
	const size = PAGE_SIZES[pageSize] || PAGE_SIZES.A4
	return orientation === 'Portrait'
		? { width: size.height, height: size.width }
		: { ...size }
}

export const FONT_FAMILIES = {
	'EB Garamond':
		'"EB Garamond", "Noto Naskh Arabic", Georgia, "Times New Roman", "Amiri", serif',
	'Noto Naskh Arabic': '"Noto Naskh Arabic", "Amiri", serif',
	Georgia: 'Georgia, "Times New Roman", "Noto Naskh Arabic", "Amiri", serif',
	Helvetica:
		'"Helvetica Neue", Helvetica, Arial, "Noto Naskh Arabic", "Amiri", serif',
}
export const DEFAULT_FONT = 'EB Garamond'

export const TEXT_FIELDS = [
	{ key: 'student_name', label: 'Student name' },
	{ key: 'course_title', label: 'Course title' },
	{ key: 'batch_title', label: 'Batch title' },
	{ key: 'start_date', label: 'Batch start date' },
	{ key: 'end_date', label: 'Batch end date' },
	{ key: 'serial_number', label: 'Serial number' },
	{ key: 'certificate_id', label: 'Certificate ID' },
	{ key: 'verification_url', label: 'Verification URL' },
	{ key: 'signer_1_name', label: 'Signer 1 name' },
	{ key: 'signer_1_title', label: 'Signer 1 title' },
	{ key: 'signer_2_name', label: 'Signer 2 name' },
	{ key: 'signer_2_title', label: 'Signer 2 title' },
	{ key: 'evaluator_name', label: 'Evaluator name' },
	{ key: 'institute_name', label: 'Institute name' },
]

export const IMAGE_FIELDS = [
	{ key: 'qr_code', label: 'QR code' },
	{ key: 'logo', label: 'Logo' },
	{ key: 'signature_1', label: 'Signature 1' },
	{ key: 'signature_2', label: 'Signature 2' },
]

export const LAYOUT_FIELDS = [...TEXT_FIELDS, ...IMAGE_FIELDS]
export const IMAGE_FIELD_KEYS = IMAGE_FIELDS.map((field) => field.key)

export const PLACEHOLDERS = [
	...TEXT_FIELDS.map((field) => ({
		key: field.key,
		description: `${field.label} (text)`,
	})),
	{ key: 'logo_url', description: 'Logo address (text)' },
	{ key: 'qr_code', description: 'QR code image (HTML)' },
	{ key: 'logo', description: 'Logo image (HTML)' },
	{ key: 'signature_1', description: 'Signature 1 image (HTML)' },
	{ key: 'signature_2', description: 'Signature 2 image (HTML)' },
]

export const SAMPLE_VALUES = {
	student_name: 'Afnan Khaled Mohammed Ali Al-Ashwal',
	course_title: 'English for Communication, Level 6A',
	batch_title: 'Batch 24 - Evening',
	start_date: '05 Jan 2026',
	end_date: '30 Mar 2026',
	serial_number: '120539',
	certificate_id: 'SAMPLE-CERTIFICATE',
	verification_url: 'https://example.com/verify/sample-verification-token',
	signer_1_name: 'Signer One',
	signer_1_title: 'Director',
	signer_2_name: 'Signer Two',
	signer_2_title: 'Academic Manager',
	evaluator_name: 'Sample Evaluator',
	institute_name: 'Faculty Language Institute',
}

export const RANGES = {
	x: { min: 0, max: 100 },
	y: { min: 0, max: 100 },
	width: { min: 1, max: 100 },
	font_size: { min: 0.5, max: 30 },
}
export const MAX_LAYOUT_ELEMENTS = 60
export const DEFAULT_ELEMENT = {
	x: 35,
	y: 40,
	width: 30,
	font_size: 3,
	font_family: '',
	color: '#000000',
	align: 'center',
	bold: false,
	italic: false,
}

export const clamp = (value, { min, max }) =>
	Math.min(max, Math.max(min, Number.isFinite(value) ? value : min))
